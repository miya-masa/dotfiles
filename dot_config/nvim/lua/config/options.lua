-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.opt.ttimeoutlen = 5
vim.opt.swapfile = false
vim.opt.writebackup = false
vim.opt.clipboard = "unnamedplus"

-- OSC 52 の read query (ESC ] 52 ; c ; ?) に応答する端末が経路上にいない。
-- tmux は自分の paste buffer から即答していたが、herdr は write を上位端末へ
-- 中継するだけで query には答えない。'clipboard' が unnamedplus なので put の
-- たびに + レジスタの取得が走り、そのつど nvim が 10 秒待ってタイムアウトする
-- （nvim 自身も自動検出では 'clipboard' 設定時に OSC 52 を選ばない）。
-- copy だけ OSC 52 に載せ、paste は nvim 内の無名レジスタから返す。
-- 端末側でコピーした文字列を貼るときは端末のペースト操作を使う。
local function paste_from_unnamed()
  return { vim.fn.getreg('"', 1, true), vim.fn.getregtype('"') }
end

vim.g.clipboard = {
  name = "OSC 52 (copy only)",
  copy = {
    ["+"] = require("vim.ui.clipboard.osc52").copy("+"),
    ["*"] = require("vim.ui.clipboard.osc52").copy("*"),
  },
  paste = {
    ["+"] = paste_from_unnamed,
    ["*"] = paste_from_unnamed,
  },
}

vim.api.nvim_create_user_command("UpdateDisplay", function()
  if vim.env.TMUX == nil then
    return
  end
  local display = vim.fn.system("tmux show-env DISPLAY")
  if vim.v.shell_error == 0 then
    vim.env.DISPLAY = display:gsub("^DISPLAY=", ""):gsub("\n", "")
  else
    print("Failed to update DISPLAY variable.")
  end
end, {})

-- Agent bridge: herdr workspace ごとに固定パスの RPC socket を listen し、
-- ペイン ID を registry に残す。Agent 側 (nvim-review-open) がこの socket に
-- 繋いで diffview を開いたり外部変更を reload したりする。
-- workspace の外（tmux / 素の端末）では何もしない。
-- $EDITOR として一瞬だけ起動する nvim。これに socket を取られると、その間に
-- 立ち上げた本命の nvim が登録できず、agent が commit message 編集中の nvim へ
-- diff を開いてしまう。
local throwaway_editor_targets = {
  "COMMIT_EDITMSG",
  "MERGE_MSG",
  "TAG_EDITMSG",
  "git%-rebase%-todo",
  "addp%-hunk%-edit%.diff",
}

local function is_throwaway_editor()
  for i = 0, vim.fn.argc() - 1 do
    local name = vim.fn.argv(i)
    for _, pattern in ipairs(throwaway_editor_targets) do
      if name:match(pattern) then
        return true
      end
    end
  end
  return false
end

local function start_agent_bridge_server()
  local ws = vim.env.HERDR_WORKSPACE_ID
  if not ws or ws == "" or is_throwaway_editor() then
    return
  end

  local dir = vim.fs.joinpath(vim.fn.stdpath("state"), "servers")
  vim.fn.mkdir(dir, "p")
  local sock = vim.fs.joinpath(dir, ws .. ".sock")

  -- 既存 socket に繋がるなら同じ workspace で別の nvim が先に listen している
  -- ので譲る。繋がらなければ stale なので消す（残っていると serverstart が
  -- address in use で失敗する）。
  if vim.uv.fs_stat(sock) then
    local ok, chan = pcall(vim.fn.sockconnect, "pipe", sock, { rpc = true })
    if ok and chan ~= 0 then
      pcall(vim.fn.chanclose, chan)
      return
    end
    os.remove(sock)
  end

  if not pcall(vim.fn.serverstart, sock) then
    return
  end

  local registry = io.open(vim.fs.joinpath(dir, ws .. ".json"), "w")
  if registry then
    registry:write(vim.json.encode({
      socket = sock,
      pane_id = vim.env.HERDR_PANE_ID,
      pid = vim.fn.getpid(),
      cwd = vim.uv.cwd(),
    }))
    registry:close()
  end
  return true
end

if not start_agent_bridge_server() then
  -- 譲った相手が先に終わることがある（短命の $EDITOR、別ペインの nvim）。
  -- その場合 socket は消えるので、フォーカスが戻ったときに取り直す。
  vim.api.nvim_create_autocmd("FocusGained", {
    group = vim.api.nvim_create_augroup("AgentBridgeServer", { clear = true }),
    callback = function()
      if start_agent_bridge_server() then
        return true
      end
    end,
  })
end
