-- Neovim -> Agent の橋渡し。
--
-- herdr の同じ workspace で走っている Claude Code / Codex のペインへ、今見て
-- いる場所やレビュー指摘を投入する。Agent の起動・一覧・状態表示は herdr の
-- サイドバーの仕事なので、ここには持ち込まない（持つのは「送る」1 方向だけ）。
--
-- 逆方向（Agent -> Neovim）は Agent 側が ~/.local/bin/nvim-review-open を呼び、
-- config/options.lua が listen している RPC socket 経由で diffview を開く。

local M = {}

--- herdr CLI はエラー時に exit 1 を返し、stderr へ
--- `{"error":{"code":...,"message":...},"id":...}` を 1 行出す。生の JSON を
--- そのまま notify に流すと読めないので message だけ取り出す。
---@param args string[]
---@return string|nil stdout
---@return string|nil error
local function herdr(args)
  local cmd = { "herdr" }
  vim.list_extend(cmd, args)
  local result = vim.system(cmd, { text = true }):wait()

  if result.code ~= 0 then
    local stderr = vim.trim(result.stderr or "")
    local ok, decoded = pcall(vim.json.decode, stderr)
    if ok and type(decoded) == "table" and type(decoded.error) == "table" and decoded.error.message then
      return nil, decoded.error.message
    end
    return nil, stderr ~= "" and stderr or "herdr command failed"
  end

  return vim.trim(result.stdout or ""), nil
end

---@param args string[]
---@return string|nil stdout
local function git(args)
  local root = M.repo_root()
  if not root then
    return nil
  end
  local cmd = { "git", "-C", root }
  vim.list_extend(cmd, args)
  local result = vim.system(cmd, { text = true }):wait()
  if result.code ~= 0 then
    return nil
  end
  return vim.trim(result.stdout or "")
end

--- 現在のバッファが属する Git worktree の root
---@return string|nil
function M.repo_root()
  local name = vim.api.nvim_buf_get_name(0)
  local start = (name ~= "" and not name:match("^%a[%w+.-]*://")) and vim.fs.dirname(name) or vim.uv.cwd()
  local root = vim.fs.root(start, ".git")
  return root and vim.fs.normalize(root) or nil
end

--- default branch との merge-base。diff の起点。
---@return string|nil
function M.base_rev()
  local head = git({ "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD" })
  local candidates = {}
  if head then
    table.insert(candidates, (head:gsub("^refs/remotes/", "")))
  end
  vim.list_extend(candidates, { "origin/main", "origin/master", "main", "master" })

  for _, candidate in ipairs(candidates) do
    local base = git({ "merge-base", candidate, "HEAD" })
    if base and base ~= "" then
      return base
    end
  end
  return nil
end

--- workspace 内の agent ペインを列挙する（自分自身は除く）
---@return table[]
local function agent_panes()
  local ws = vim.env.HERDR_WORKSPACE_ID
  if not ws or ws == "" then
    return {}
  end

  local out, err = herdr({ "pane", "list", "--workspace", ws })
  if not out then
    vim.notify(("herdr pane list failed: %s"):format(err or "unknown"), vim.log.levels.ERROR)
    return {}
  end

  local ok, decoded = pcall(vim.json.decode, out)
  if not ok then
    return {}
  end

  return vim.tbl_filter(function(pane)
    return pane.agent ~= nil and pane.pane_id ~= vim.env.HERDR_PANE_ID
  end, vim.tbl_get(decoded, "result", "panes") or {})
end

--- 貼った先で続きを書けるようフォーカスも移す。herdr CLI の `pane focus` は
--- 方向指定しか受け取らないので socket API を直接叩く。人間がキーを押して
--- 呼んだ経路なので、対象は必ず今見ている workspace にある。
---@param pane_id string
local function focus_pane(pane_id)
  vim.system({ "herdr-api", "pane.focus", vim.json.encode({ pane_id = pane_id }) }, { text = true }):wait()
end

---@param pane table
---@param text string
---@param submit boolean 送信まで確定するか
local function deliver(pane, text, submit)
  -- context は貼るだけにする。`agent prompt` は本文と Enter を atomically 送る
  -- ので、@file だけが独り歩きして agent が動き出してしまう。続きの指示を
  -- 書き足せるよう、貼る側は Enter を送らない `pane send-text` を使う。
  local args = submit and { "agent", "prompt", pane.pane_id, text }
    or { "pane", "send-text", pane.pane_id, text }

  local _, err = herdr(args)
  if err then
    vim.notify(("failed to send to %s: %s"):format(pane.agent, err), vim.log.levels.ERROR)
    return
  end

  focus_pane(pane.pane_id)
  vim.notify(
    ("%s %s (%s)"):format(submit and "submitted to" or "pasted into", pane.agent, pane.pane_id),
    vim.log.levels.INFO
  )
end

--- agent ペインへテキストを渡す。複数居れば選ばせる。
---@param text string
---@param submit? boolean 既定は false（貼るだけ）
function M.send(text, submit)
  local panes = agent_panes()

  if #panes == 0 then
    vim.notify("no agent pane in this herdr workspace", vim.log.levels.WARN)
    return
  end

  if #panes == 1 then
    deliver(panes[1], text, submit or false)
    return
  end

  vim.ui.select(panes, {
    prompt = submit and "Submit to agent:" or "Paste into agent:",
    format_item = function(pane)
      return ("%s  %s  [%s]"):format(pane.pane_id, pane.agent, pane.agent_status or "?")
    end,
  }, function(choice)
    if choice then
      deliver(choice, text, submit or false)
    end
  end)
end

--- 現在ファイルの repo 相対パス
---@return string|nil
local function relative_path()
  local name = vim.api.nvim_buf_get_name(0)
  if name == "" or name:match("^%a[%w+.-]*://") then
    return nil
  end
  local root = M.repo_root()
  local file = vim.fs.normalize(vim.fn.fnamemodify(name, ":p"))
  return root and vim.fs.relpath(root, file) or file
end

--- 選択範囲を `@file#Lstart-Lend` で送る
function M.send_selection()
  local path = relative_path()
  if not path then
    vim.notify("this buffer has no file to send", vim.log.levels.WARN)
    return
  end

  local start_line = vim.fn.line("v")
  local end_line = vim.fn.line(".")
  if start_line > end_line then
    start_line, end_line = end_line, start_line
  end

  M.send(("@%s#L%d-%d "):format(path, start_line, end_line))
end

--- 現在ファイルを `@file` で送る
function M.send_file()
  local path = relative_path()
  if not path then
    vim.notify("this buffer has no file to send", vim.log.levels.WARN)
    return
  end
  M.send("@" .. path .. " ")
end

--- base からの変更ファイル一覧を送る
function M.send_changed_files()
  local base = M.base_rev()
  if not base then
    vim.notify("failed to resolve the base revision", vim.log.levels.WARN)
    return
  end

  -- quotePath 既定 (true) だと非 ASCII のパスが "\346\227\245..." で出るので切る。
  -- untracked は diff に出ないので別に足す (agent は新規ファイルを足しがち)。
  local tracked = git({ "-c", "core.quotePath=false", "diff", "--name-only", base }) or ""
  local untracked = git({ "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard" }) or ""

  local files = {}
  for _, path in ipairs(vim.split(tracked .. "\n" .. untracked, "\n")) do
    if path ~= "" then
      table.insert(files, "@" .. path)
    end
  end
  if #files == 0 then
    vim.notify("no changes against the base", vim.log.levels.INFO)
    return
  end
  M.send(table.concat(files, " ") .. " ")
end

--- .review に溜めた指摘への対応を依頼する
function M.request_review_response()
  local root = M.repo_root()
  if not root then
    vim.notify("not inside a Git worktree", vim.log.levels.WARN)
    return
  end

  local review_file = vim.fs.joinpath(root, ".review", "review_comments.yaml")
  if not vim.uv.fs_stat(review_file) then
    vim.notify("no review comments yet (.review/review_comments.yaml)", vim.log.levels.WARN)
    return
  end

  -- これは完結した依頼なので、貼るだけでなく送信まで確定する。
  M.send("review-respond で .review/review_comments.yaml の pending なレビュー指摘に対応してください。", true)
end

--- base..作業ツリー の diffview を開く（Agent が開くのと同じ範囲）
function M.open_review_diff()
  local base = M.base_rev()
  if not base then
    vim.notify("failed to resolve the base revision", vim.log.levels.WARN)
    return
  end

  -- パスに空白が入ると ex コマンドの引数分割で壊れるので escape する。
  local root = M.repo_root()
  vim.cmd(("DiffviewOpen %s%s"):format(base, root and (" -C" .. vim.fn.fnameescape(root)) or ""))
end

return M
