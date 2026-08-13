local M = {}

local categories = {
  must = true,
  imo = true,
  q = true,
}

local context_line_count = 2

---@param root string
---@param args string[]
---@return string|nil output
---@return string|nil error
local function git(root, args)
  local cmd = { "git", "-C", root }
  vim.list_extend(cmd, args)
  local result = vim.system(cmd, { text = true }):wait()
  if result.code ~= 0 then
    return nil, vim.trim(result.stderr or "git command failed")
  end
  return vim.trim(result.stdout or ""), nil
end

---@param bufnr integer
---@return boolean
local function is_codediff_original(bufnr)
  if vim.g.loaded_codediff ~= 1 then
    return false
  end

  local ok, lifecycle = pcall(require, "codediff.ui.lifecycle")
  if not ok then
    return false
  end

  local original = lifecycle.get_buffers(vim.api.nvim_get_current_tabpage())
  return original == bufnr
end

--- Resolve the absolute file path and its Git worktree root
---@return table|nil target
---@return string|nil error
local function get_target()
  local bufnr = vim.api.nvim_get_current_buf()
  local name = vim.api.nvim_buf_get_name(bufnr)
  if
    name == ""
    or vim.bo[bufnr].buftype ~= ""
    or name:match("^%a[%w+.-]*://")
    or is_codediff_original(bufnr)
  then
    return nil, "Review comments can only be added to working-tree files"
  end

  if vim.bo[bufnr].modified then
    return nil, "Save the file before adding a review comment"
  end

  local file = vim.fs.normalize(vim.fn.fnamemodify(name, ":p"))
  local review_root = vim.fs.root(file, ".git")
  if not review_root then
    return nil, "Review comments require a file inside a Git worktree"
  end

  local relative_file = vim.fs.relpath(review_root, file)
  if not relative_file then
    return nil, "Failed to resolve the review file relative to its worktree"
  end

  local head_sha, head_err = git(review_root, { "rev-parse", "HEAD" })
  if not head_sha then
    return nil, ("Failed to resolve Git HEAD: %s"):format(head_err or "unknown error")
  end

  local file_blob, blob_err = git(review_root, { "hash-object", "--", relative_file })
  if not file_blob then
    return nil, ("Failed to hash the review file: %s"):format(blob_err or "unknown error")
  end

  return {
    bufnr = bufnr,
    file = file,
    display_file = relative_file,
    relative_file = relative_file,
    review_root = vim.fs.normalize(review_root),
    capture_head_sha = head_sha,
    capture_file_blob = file_blob,
  }
end

---@param target table
---@param start_line integer
---@param end_line integer
---@return table
local function snapshot_range(target, start_line, end_line)
  local line_count = vim.api.nvim_buf_line_count(target.bufnr)
  local before_start = math.max(0, start_line - context_line_count - 1)
  local after_end = math.min(line_count, end_line + context_line_count)

  return {
    reviewed_text = table.concat(vim.api.nvim_buf_get_lines(target.bufnr, start_line - 1, end_line, false), "\n"),
    context_before = vim.api.nvim_buf_get_lines(target.bufnr, before_start, start_line - 1, false),
    context_after = vim.api.nvim_buf_get_lines(target.bufnr, end_line, after_end, false),
  }
end

--- Get range from Normal mode cursor position
---@return table|nil range
---@return string|nil error
function M.get_range_normal()
  local target, err = get_target()
  if not target then
    return nil, err
  end

  local pos = vim.api.nvim_win_get_cursor(0)
  local range = {
    file = target.file,
    display_file = target.display_file,
    relative_file = target.relative_file,
    review_root = target.review_root,
    capture_head_sha = target.capture_head_sha,
    capture_file_blob = target.capture_file_blob,
    start_line = pos[1],
    start_col = pos[2] + 1,
    end_line = pos[1],
    end_col = pos[2] + 1,
  }
  return vim.tbl_extend("force", range, snapshot_range(target, range.start_line, range.end_line))
end

--- Get range from Visual mode selection
---@return table|nil range
---@return string|nil error
function M.get_range_visual()
  local target, err = get_target()
  if not target then
    return nil, err
  end

  local sl = vim.fn.line("v")
  local sc = vim.fn.col("v")
  local el = vim.fn.line(".")
  local ec = vim.fn.col(".")
  if sl > el or (sl == el and sc > ec) then
    sl, sc, el, ec = el, ec, sl, sc
  end
  local range = {
    file = target.file,
    display_file = target.display_file,
    relative_file = target.relative_file,
    review_root = target.review_root,
    capture_head_sha = target.capture_head_sha,
    capture_file_blob = target.capture_file_blob,
    start_line = sl,
    start_col = sc,
    end_line = el,
    end_col = ec,
  }
  return vim.tbl_extend("force", range, snapshot_range(target, range.start_line, range.end_line))
end

---@param dir string
---@param callback fun(): nil
---@return boolean
local function with_review_lock(dir, callback)
  local lock_dir = vim.fs.joinpath(dir, ".lock")
  if vim.fn.mkdir(lock_dir) ~= 1 then
    vim.notify(("Review data is busy; remove stale lock only after checking: %s"):format(lock_dir), vim.log.levels.ERROR)
    return false
  end

  local ok, err = pcall(callback)
  vim.fn.delete(lock_dir, "d")
  if not ok then
    vim.notify(("Failed to save review comment: %s"):format(err), vim.log.levels.ERROR)
    return false
  end
  return true
end

---@param filepath string
---@param content string
local function atomic_write(filepath, content)
  local tmp = ("%s.%d.%s.tmp"):format(filepath, vim.fn.getpid(), tostring(vim.uv.hrtime()))
  local f, open_err = io.open(tmp, "w")
  assert(f, open_err or "failed to open temporary review file")
  f:write(content)
  f:close()
  local ok, rename_err = os.rename(tmp, filepath)
  assert(ok, rename_err or "failed to replace review file")
end

--- Save a review entry as YAML
---@param range table
---@param comment string
---@param category "must"|"imo"|"q"
function M.save_yaml(range, comment, category)
  assert(categories[category], "invalid review category")

  local dir = vim.fs.joinpath(range.review_root, ".review")
  local filepath = vim.fs.joinpath(dir, "review_comments.yaml")

  vim.fn.mkdir(dir, "p")

  local timestamp = os.date("%Y-%m-%dT%H:%M:%S%z")
  local entry_id = vim.fn.sha256(table.concat({
    range.file,
    timestamp,
    tostring(vim.uv.hrtime()),
    comment,
  }, "\0"))
  local comment_lines = vim.split(comment, "\n")
  local indented = {}
  for _, line in ipairs(comment_lines) do
    table.insert(indented, "      " .. line)
  end
  local comment_yaml = table.concat(indented, "\n") .. "\n"

  local entry = string.format(
    [[  - id: %s
    file: %s
    relative_file: %s
    category: %s
    status: pending
    capture_head_sha: %s
    capture_file_blob: %s
    reviewed_text: %s
    context_before: %s
    context_after: %s
    start_line: %d
    end_line: %d
    start_col: %d
    end_col: %d
    timestamp: "%s"
    comment: |
%s]],
    vim.json.encode(entry_id),
    vim.json.encode(range.file),
    vim.json.encode(range.relative_file),
    category,
    vim.json.encode(range.capture_head_sha),
    vim.json.encode(range.capture_file_blob),
    vim.json.encode(range.reviewed_text),
    vim.json.encode(range.context_before),
    vim.json.encode(range.context_after),
    range.start_line,
    range.end_line,
    range.start_col,
    range.end_col,
    timestamp,
    comment_yaml
  )

  if not with_review_lock(dir, function()
    local existing = ""
    local current = io.open(filepath, "r")
    if current then
      existing = current:read("*a")
      current:close()
    end
    if existing == "" then
      existing = "reviews:\n"
    end
    atomic_write(filepath, existing .. entry)
  end) then
    return
  end

  vim.notify(("Review comment saved [%s]"):format(category), vim.log.levels.INFO)
end

--- Open the review comment popup
---@param call_mode string "n" or "v"
---@param category? "must"|"imo"|"q"
function M.open(call_mode, category)
  category = category or "imo"
  assert(categories[category], "invalid review category")

  local range, err
  if call_mode == "v" then
    range, err = M.get_range_visual()
  else
    range, err = M.get_range_normal()
  end

  if not range then
    vim.notify(err or "Failed to resolve review target", vim.log.levels.ERROR)
    return
  end

  local title = string.format(
    " Review: %s L%d:%d-L%d:%d [%s] ",
    range.display_file,
    range.start_line, range.start_col,
    range.end_line, range.end_col,
    category
  )

  Snacks.win({
    title = title,
    title_pos = "center",
    footer = " <CR>: save  q: cancel ",
    footer_pos = "center",
    position = "float",
    relative = "editor",
    width = 80,
    height = 10,
    border = "rounded",
    backdrop = 60,
    enter = true,
    bo = {
      modifiable = true,
      filetype = "markdown",
    },
    wo = {
      wrap = true,
      linebreak = true,
    },
    keys = {
      ["<CR>"] = {
        function(self)
          local comment = vim.trim(self:text())
          if comment == "" then
            self:close()
            return
          end
          M.save_yaml(range, comment, category)
          self:close()
        end,
        desc = "Save",
        mode = "n",
      },
      q = "close",
    },
    on_win = function()
      vim.cmd("startinsert")
    end,
  })
end

return {
  "folke/snacks.nvim",
  _review = M,
  keys = {
    { "<leader>rc", function() M.open("n", "imo") end, desc = "Review Comment (imo)", mode = "n" },
    { "<leader>rc", function() M.open("v", "imo") end, desc = "Review Comment (imo)", mode = "v" },
    { "<leader>rm", function() M.open("n", "must") end, desc = "Review Comment (must)", mode = "n" },
    { "<leader>rm", function() M.open("v", "must") end, desc = "Review Comment (must)", mode = "v" },
    { "<leader>rq", function() M.open("n", "q") end, desc = "Review Comment (question)", mode = "n" },
    { "<leader>rq", function() M.open("v", "q") end, desc = "Review Comment (question)", mode = "v" },
  },
}
