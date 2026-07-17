local M = {}

--- Build the file path relative to CWD
---@return string
local function get_file()
  local file = vim.fn.expand("%:.")
  if file == "" then
    return "[untitled]"
  end
  return file
end

--- Get range from Normal mode cursor position
---@return table
function M.get_range_normal()
  local pos = vim.api.nvim_win_get_cursor(0)
  return {
    file = get_file(),
    start_line = pos[1],
    start_col = pos[2] + 1,
    end_line = pos[1],
    end_col = pos[2] + 1,
  }
end

--- Get range from Visual mode selection
---@return table
function M.get_range_visual()
  local sl = vim.fn.line("v")
  local sc = vim.fn.col("v")
  local el = vim.fn.line(".")
  local ec = vim.fn.col(".")
  if sl > el or (sl == el and sc > ec) then
    sl, sc, el, ec = el, ec, sl, sc
  end
  return {
    file = get_file(),
    start_line = sl,
    start_col = sc,
    end_line = el,
    end_col = ec,
  }
end

--- Save a review entry as YAML
---@param range table { file, start_line, end_line, start_col, end_col }
---@param comment string
function M.save_yaml(range, comment)
  local dir = vim.fn.getcwd() .. "/.review"
  local filepath = dir .. "/review_comments.yaml"

  vim.fn.mkdir(dir, "p")

  local timestamp = os.date("%Y-%m-%dT%H:%M:%S%z")
  local comment_lines = vim.split(comment, "\n")
  local indented = {}
  for _, line in ipairs(comment_lines) do
    table.insert(indented, "      " .. line)
  end
  local comment_yaml = table.concat(indented, "\n") .. "\n"

  local entry = string.format(
    [[  - file: %s
    start_line: %d
    end_line: %d
    start_col: %d
    end_col: %d
    severity: medium
    timestamp: "%s"
    comment: |
%s]],
    range.file,
    range.start_line,
    range.end_line,
    range.start_col,
    range.end_col,
    timestamp,
    comment_yaml
  )

  local f = io.open(filepath, "a")
  if not f then
    vim.notify("Failed to save review comment", vim.log.levels.ERROR)
    return
  end
  if f:seek("end") == 0 then
    f:write("reviews:\n")
  end
  f:write(entry)
  f:close()

  vim.notify("Review comment saved", vim.log.levels.INFO)
end

--- Open the review comment popup
---@param call_mode string "n" or "v"
function M.open(call_mode)
  local range
  if call_mode == "v" then
    range = M.get_range_visual()
  else
    range = M.get_range_normal()
  end

  local title = string.format(
    " Review: %s L%d:%d-L%d:%d [medium] ",
    range.file,
    range.start_line, range.start_col,
    range.end_line, range.end_col
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
          M.save_yaml(range, comment)
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
  keys = {
    { "<leader>rc", function() M.open("n") end, desc = "Review Comment", mode = "n" },
    { "<leader>rc", function() M.open("v") end, desc = "Review Comment", mode = "v" },
  },
}
