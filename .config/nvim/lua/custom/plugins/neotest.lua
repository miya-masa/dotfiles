return {
  "nvim-neotest/neotest",
  dependencies = {
    'nvim-neotest/neotest-python',
    "nvim-neotest/neotest-go",
    -- Your other test adapters here
  },
  config = function()
    -- get neotest namespace (api call creates or returns namespace)
    local neotest_ns = vim.api.nvim_create_namespace("neotest")
    vim.diagnostic.config({
      virtual_text = {
        format = function(diagnostic)
          local message =
              diagnostic.message:gsub("\n", " "):gsub("\t", " "):gsub("%s+", " "):gsub("^%s+", "")
          return message
        end,
      },
    }, neotest_ns)
    require("neotest").setup({
      -- your neotest config here
      adapters = {
        require("neotest-go")({
          args = { "-count=1", "-timeout=60s" }
        }),
        require("neotest-python"),
      },
      floating = {
        border = "rounded",
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
  end,
}
