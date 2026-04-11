return {
  {
    "christoomey/vim-tmux-navigator",
    cmd = {
      "TmuxNavigateLeft",
      "TmuxNavigateDown",
      "TmuxNavigateUp",
      "TmuxNavigateRight",
      "TmuxNavigatePrevious",
      "TmuxNavigatorProcessList",
    },
    keys = {
      { "<c-h>", "<cmd><C-U>TmuxNavigateLeft<cr>" },
      { "<c-j>", "<cmd><C-U>TmuxNavigateDown<cr>" },
      { "<c-k>", "<cmd><C-U>TmuxNavigateUp<cr>" },
      { "<c-l>", "<cmd><C-U>TmuxNavigateRight<cr>" },
      { "<c-\\>", "<cmd><C-U>TmuxNavigatePrevious<cr>" },

      -- Terminal
      { "<c-h>", [[<C-\><C-n><cmd>TmuxNavigateLeft<cr>]], mode = "t" },
      { "<c-j>", [[<C-\><C-n><cmd>TmuxNavigateDown<cr>]], mode = "t" },
      { "<c-k>", [[<C-\><C-n><cmd>TmuxNavigateUp<cr>]], mode = "t" },
      { "<c-l>", [[<C-\><C-n><cmd>TmuxNavigateRight<cr>]], mode = "t" },
      { "<c-\\>", [[<C-\><C-n><cmd>TmuxNavigatePrevious<cr>]], mode = "t" },
    },
  },
  {
    "johmsalas/text-case.nvim",
    config = function()
      require("textcase").setup({})
    end,
    keys = {
      { "ga.", "<cmd>TextCaseOpenTelescope<CR>", mode = "n", desc = "Text Case" },
      { "ga.", "<cmd>TextCaseOpenTelescope<CR>", mode = "v", desc = "Text Case" },
    },
    cmd = {
      "Subs",
      "TextCaseOpenTelescope",
      "TextCaseOpenTelescopeQuickChange",
      "TextCaseOpenTelescopeLSPChange",
      "TextCaseStartReplacingCommand",
    },
  },
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewFileHistory", "DiffviewClose" },
  },
  {
    "vim-jp/vimdoc-ja",
    event = "CmdlineEnter",
  },
  {
    "jbyuki/venn.nvim",
    keys = {
      { "<leader>tv", ":lua Toggle_venn()<CR>", noremap = true, desc = "Toggle Venn" },
    },
    config = function()
      function _G.Toggle_venn()
        local venn_enabled = vim.inspect(vim.b.venn_enabled)
        if venn_enabled == "nil" then
          vim.b.venn_enabled = true
          vim.cmd([[setlocal ve=all]])
          vim.api.nvim_buf_set_keymap(0, "n", "J", "<C-v>j:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "K", "<C-v>k:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "L", "<C-v>l:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "H", "<C-v>h:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "v", "<CR>", ":VBox<CR>", { noremap = true })
          print("venn on")
        else
          vim.cmd([[setlocal ve=]])
          vim.api.nvim_buf_del_keymap(0, "n", "J")
          vim.api.nvim_buf_del_keymap(0, "n", "K")
          vim.api.nvim_buf_del_keymap(0, "n", "L")
          vim.api.nvim_buf_del_keymap(0, "n", "H")
          vim.api.nvim_buf_del_keymap(0, "v", "<CR>")
          vim.b.venn_enabled = nil
          print("venn off")
        end
      end
    end,
  },
  {
    "RaafatTurki/hex.nvim",
    cmd = { "HexDump", "HexAssemble", "HexToggle" },
    opts = {},
  },
  {
    "Wansmer/treesj",
    keys = { "<space>m", "<space>j", "<space>s" },
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    opts = {},
  },
}
