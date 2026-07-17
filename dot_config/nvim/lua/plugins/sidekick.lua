return {
  {
    "folke/sidekick.nvim",
    opts = {
      nes = { enabled = false },
      cli = {
        win = {
          keys = {
            prompt = { "<c-x>", "prompt", mode = "t", desc = "insert prompt or context" },
          },
        },
      },
    },
  },
}
