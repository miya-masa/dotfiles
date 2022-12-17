vim.g.mapleader = ","
vim.o.autoread = true
vim.o.clipboard='unnamedplus'
vim.o.viminfo='\'100,n$HOME/.vim/files/info/viminfo'
-- vim.o.formatoptions+=mM
vim.o.inccommand = split
vim.o.ambiwidth = single
vim.o.list = true
vim.o.listchars = 'tab:^\\ ,trail:~'
vim.o.expandtab = true
vim.o.smarttab = true
vim.o.shiftwidth=2
vim.o.softtabstop=2
vim.o.tabstop=4
vim.o.linebreak = true
vim.o.textwidth=500
vim.o.autoindent = true
vim.o.smartindent = true
vim.o.wrap = true
vim.o.laststatus = 2
vim.o.completeopt="menu,menuone,noselect"

local signs = { Error = "", Warn = "", Hint = "", Info = "" }

for type, icon in pairs(signs) do
  local hl = "DiagnosticSign" .. type
  vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = hl })
end
