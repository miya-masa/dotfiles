require("neotest").setup({
  adapters = {
    require("neotest-python"),
    require("neotest-go")({
      experimental = {
        test_table = true,
      },
      args = { "-count=1", "-timeout=60s", "-tags=integration" }
    })
  },
  floating = {
    max_height = 0.9,
    max_width = 0.9,
  },
  icons = {
    failed = "X",
    final_child_indent = " ",
    final_child_prefix = "╰",
    non_collapsible = "─",
    passed = "O",
    running = "-",
    running_animated = { "/", "|", "\\", "-", "/", "|", "\\", "-" },
    skipped = "-",
    unknown = "-"
  },
})

vim.keymap.set('n', 't<C-n>', ':lua require("neotest").run.run()<CR>')
vim.keymap.set('n', 'ti<C-n>', ':lua require("neotest").run.run()<CR>')
vim.keymap.set('n', 't<C-m>', ':lua require("neotest").run.stop()<CR>')
vim.keymap.set('n', 't<C-f>', ':cd %:p:h<cr>:lua require("neotest").run.run(vim.fn.expand("%"))<CR>')
vim.keymap.set('n', 't<C-t>', ':cd %:p:h<cr>:lua require("neotest").summary.toggle()<CR>')
vim.keymap.set('n', 't<C-o>', ':cd %:p:h<cr>:lua require("neotest").output.open({ enter = true })<CR>')
vim.keymap.set('n', '[n', '<cmd>lua require("neotest").jump.prev({ status = "failed" })<CR>')
vim.keymap.set('n', ']n', '<cmd>lua require("neotest").jump.next({ status = "failed" })<CR>')
