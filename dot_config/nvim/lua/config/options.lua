-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.mapleader = ","
vim.opt.swapfile = false
vim.opt.writebackup = false
vim.opt.clipboard = "unnamedplus"
vim.g.clipboard = "osc52"

vim.api.nvim_create_user_command("UpdateDisplay", function()
  local display = vim.fn.system("tmux show-env DISPLAY")
  if vim.v.shell_error == 0 then
    vim.env.DISPLAY = display:gsub("^DISPLAY=", ""):gsub("\n", "")
  else
    print("Failed to update DISPLAY variable.")
  end
end, {})
vim.opt.swapfile = false
