vim.g.mapleader = ","
vim.opt.autoread = true
vim.opt.clipboard = 'unnamedplus'
vim.opt.viminfo = '\'100,n' .. os.getenv("HOME") .. '/.vim/files/info/viminfo'
vim.opt.undofile = true
vim.opt.undodir = os.getenv("HOME") .. '/undodir'
-- vim.o.formatoptions+=mM
vim.opt.inccommand = 'split'
vim.opt.ambiwidth = 'single'
vim.opt.list = true
vim.opt.listchars = 'tab:^\\ ,trail:~'
vim.opt.expandtab = true
vim.opt.smarttab = true
vim.opt.shiftwidth = 2
vim.opt.softtabstop = 2
vim.opt.tabstop = 4
vim.opt.linebreak = true
vim.opt.textwidth = 500
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.wrap = true
vim.opt.laststatus = 2
vim.opt.completeopt = { "menu", "menuone", "noselect" }
vim.opt.swapfile = false
vim.opt.writebackup = false
vim.opt.backup = false
vim.opt.display = 'lastline'
vim.opt.scrolloff = 7
vim.opt.number = true

local signs = { Error = "", Warn = "", Hint = "", Info = "" }

for type, icon in pairs(signs) do
  local hl = "DiagnosticSign" .. type
  vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = hl })
end
