require("neotest").setup({
  adapters = {
    require("neotest-python"),
    require("neotest-go")({
      experimental = {
        test_table = true,
      },
      args = { "-count=1", "-timeout=60s" , "-tags=integration"}
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
