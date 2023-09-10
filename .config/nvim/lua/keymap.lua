vim.keymap.set('n', 'ZZ', '<Nop>')
vim.keymap.set('n', 'Y', 'y$')
vim.keymap.set('n', '<Leader>-', ':split<CR>')
--
vim.keymap.set('n', '<C-q>', '<Plug>(quickrun)<CR>')
vim.keymap.set('n', '<leader>p', ':call print_debug#print_debug()<cr>')
--
vim.keymap.set('c', '<C-H>', '<BS>')
vim.keymap.set('c', '<C-F>', '<Right>')
vim.keymap.set('c', '<C-B>', '<Left>')
--

vim.keymap.set('v', '*', ':<C-u>call VisualSelection(\'\', \'\')<CR>/<C-R>=@/<CR><CR>')
vim.keymap.set('v', '#', ':<C-u>call VisualSelection(\'\', \'\')<CR>?<C-R>=@/<CR><CR>')
-- " Disable highlight when <leader><cr> is pressed
vim.keymap.set('', '<leader><cr>', ':noh<cr>')
-- " Smart way to move between windows
-- vim.keymap.set('', '<C-j>', '<C-W>j')
-- vim.keymap.set('', '<C-k>', '<C-W>k')
-- vim.keymap.set('', '<C-h>', '<C-W>h')
-- vim.keymap.set('', '<C-l>', '<C-W>l')
vim.keymap.set('', '0', '^')
-- vim.keymap.set('', '<leader>ss', ':setlocal spell!<cr>')
vim.keymap.set('', '<leader>sa', 'zg')
vim.keymap.set('', '<leader>s?', 'z=')
vim.keymap.set('', '<Leader>m', 'mmHmt:%s/<C-V><cr>//ge<cr>\'tzt\'m')
