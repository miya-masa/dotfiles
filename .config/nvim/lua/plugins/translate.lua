require("translate").setup({
    default = {
        command = "translate_shell",
    },
    preset = {
        output = {
            split = {
                append = true,
            },
        },
    },
})

vim.keymap.set('n', '<Leader>tsf', '<Cmd>Translate JA<CR>')
vim.keymap.set('n', '<Leader>tsr', '<Cmd>Translate JA --output=replace<CR>')
vim.keymap.set('x', '<Leader>tsf', '<Cmd>Translate JA<CR>')
vim.keymap.set('x', '<Leader>tsr', '<Cmd>Translate JA --output=replace<CR>')
vim.keymap.set('n', '<Leader>tsF', '<Cmd>Translate EN<CR>')
vim.keymap.set('n', '<Leader>tsR', '<Cmd>Translate EN --output=replace<CR>')
vim.keymap.set('x', '<Leader>tsF', '<Cmd>Translate EN<CR>')
vim.keymap.set('x', '<Leader>tsR', '<Cmd>Translate EN --output=replace<CR>')
