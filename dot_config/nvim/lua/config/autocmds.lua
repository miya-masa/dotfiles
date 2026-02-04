-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")
-- Terminalウィンドウに入ったら常にTerminalモード(Insert)にする

vim.api.nvim_create_autocmd({ "FocusGained", "TermOpen" }, {
  group = vim.api.nvim_create_augroup("TerminalAutoInsertOnFocus", { clear = true }),
  callback = function()
    local buf = vim.api.nvim_get_current_buf()
    if vim.bo[buf].buftype == "terminal" then
      -- タイミング負け対策
      vim.schedule(function()
        -- すでにinsertなら何もしない
        local m = vim.api.nvim_get_mode().mode
        if vim.bo[buf].buftype == "terminal" and not m:match("i") then
          vim.cmd("startinsert")
        end
      end)
    end
  end,
})

-- diffview:// など「実ファイルではない」バッファでLSPを無効化する
vim.api.nvim_create_autocmd({ "BufNewFile", "BufReadPre", "BufEnter" }, {
  callback = function(ev)
    local name = vim.api.nvim_buf_get_name(ev.buf)
    if name:match("^diffview://") then
      vim.b[ev.buf].lsp_disable = true
      -- 念のため既にattach済みなら外す（環境差の保険）
      for _, c in ipairs(vim.lsp.get_clients({ bufnr = ev.buf })) do
        vim.lsp.buf_detach_client(ev.buf, c.id)
      end
    end
  end,
})
