return {
  {
    "snacks.nvim",
    opts = {
      animate = {
        enabled = false,
      },
      scroll = {
        animate = {
          duration = { step = 15, total = 25 },
        },
      },
      indent = {
        animate = {
          enabled = false,
        },
      },
      terminal = {
        win = {
          keys = {
            nav_h = { "<C-h>", [[<C-\><C-n><Cmd>TmuxNavigateLeft<CR>]], desc = "Tmux Navigate Left", mode = "t" },
            nav_j = { "<C-j>", [[<C-\><C-n><Cmd>TmuxNavigateDown<CR>]], desc = "Tmux Navigate Down", mode = "t" },
            nav_k = { "<C-k>", [[<C-\><C-n><Cmd>TmuxNavigateUp<CR>]], desc = "Tmux Navigate Up", mode = "t" },
            nav_l = { "<C-l>", [[<C-\><C-n><Cmd>TmuxNavigateRight<CR>]], desc = "Tmux Navigate Right", mode = "t" },
          },
        },
      },
    },
  },
}
