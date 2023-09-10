return {
  "bkad/CamelCaseMotion",
  config = function()
    vim.keymap.set('', 'w', '<Plug>CamelCaseMotion_w', { silent = true })
    vim.keymap.set('', 'b', '<Plug>CamelCaseMotion_b', { silent = true })
    vim.keymap.set('', 'e', '<Plug>CamelCaseMotion_e', { silent = true })
    vim.keymap.set('', 'ge', '<Plug>CamelCaseMotion_ge', { silent = true })
    vim.keymap.set({ 'o', 'x' }, 'iw', '<Plug>CamelCaseMotion_iw', { silent = true })
    vim.keymap.set({ 'o', 'x' }, 'ib', '<Plug>CamelCaseMotion_ib', { silent = true })
    vim.keymap.set({ 'o', 'x' }, 'ie', '<Plug>CamelCaseMotion_ie', { silent = true })
    vim.keymap.set('', '<Leader>cc', '<Plug>(operator-camelize)')
    vim.keymap.set('', '<Leader>C', '<Plug>(operator-decamelize)')
    vim.keymap.set('', '!', '<Plug>(operator-replace)')
  end,
}
