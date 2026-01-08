-- since this is nust an example spec, don't actually load anything here and return an empty spec
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
    dependencies = { "nvim-telescope/telescope.nvim" },
    config = function()
      require("textcase").setup({})
      require("telescope").load_extension("textcase")
      vim.api.nvim_set_keymap("n", "ga.", "<cmd>TextCaseOpenTelescope<CR>", { desc = "Telescope" })
      vim.api.nvim_set_keymap("v", "ga.", "<cmd>TextCaseOpenTelescope<CR>", { desc = "Telescope" })
    end,
    cmd = {
      -- NOTE: The Subs command name can be customized via the option "substitute_command_name"
      "Subs",
      "TextCaseOpenTelescope",
      "TextCaseOpenTelescopeQuickChange",
      "TextCaseOpenTelescopeLSPChange",
      "TextCaseStartReplacingCommand",
    },
    -- If you want to use the interactive feature of the `Subs` command right away, text-case.nvim
    -- has to be loaded on startup. Otherwise, the interactive feature of the `Subs` will only be
    -- available after the first executing of it or after a keymap of text-case.nvim has been used.
  },
  {
    "mistweaverco/kulala.nvim",
    keys = {
      { "<leader>Re", '<cmd>lua require("kulala").set_selected_env()<cr>', desc = "Select environment", ft = "http" },
    },
    opts = {},
  },
  {
    "sindrets/diffview.nvim",
  },
  {
    "simeji/winresizer",
  },
  {
    "tmux-plugins/vim-tmux-focus-events",
  },
  {
    "vim-jp/vimdoc-ja",
    keys = {
      { "h", mode = "c" },
    },
  },
  {
    "jbyuki/venn.nvim",
    config = function()
      -- venn.nvim: enable or disable keymappings
      function _G.Toggle_venn()
        local venn_enabled = vim.inspect(vim.b.venn_enabled)
        if venn_enabled == "nil" then
          vim.b.venn_enabled = true
          vim.cmd([[setlocal ve=all]])
          -- draw a line on HJKL keystokes
          vim.api.nvim_buf_set_keymap(0, "n", "J", "<C-v>j:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "K", "<C-v>k:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "L", "<C-v>l:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "H", "<C-v>h:VBox<CR>", { noremap = true })
          -- draw a box by pressing "f" with visual selection
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
      vim.api.nvim_set_keymap("n", "<leader>tv", ":lua Toggle_venn()<CR>", { noremap = true })
    end,
  },
  {
    "RaafatTurki/hex.nvim",
    opts = {},
  },
  {
    "f-person/git-blame.nvim",
    opts = {
      enabled = false,
    },
  },
  {
    "chrisgrieser/nvim-spider",
    lazy = true,
    keys = {
      {
        "e",
        "<cmd>lua require('spider').motion('e')<CR>",
        mode = { "n", "o", "x" },
      },
      {
        "w",
        "<cmd>lua require('spider').motion('w')<CR>",
        mode = { "n", "o", "x" },
      },
      {
        "b",
        "<cmd>lua require('spider').motion('b')<CR>",
        mode = { "n", "o", "x" },
      },
    },
  },
  {
    -- 'tpope/vim-dispatch',
    "buoto/gotests-vim",
    config = function()
      vim.g.gotests_template = "testify"
    end,
  },
  {
    "Wansmer/treesj",
    keys = { "<space>m", "<space>j", "<space>s" },
    dependencies = { "nvim-treesitter/nvim-treesitter" }, -- if you install parsers with `nvim-treesitter`
    opts = {},
  },
  {
    "kazhala/close-buffers.nvim",
    config = function()
      require("close_buffers").setup({
        filetype_ignore = { "neo-tree", "lazy" },
      })
      vim.api.nvim_set_keymap(
        "n",
        "<space>bda",
        [[<CMD>lua require('close_buffers').delete({type = 'hidden'})<CR>]],
        { noremap = true, silent = true }
      )
      vim.api.nvim_set_keymap(
        "n",
        "<space>bdt",
        [[<CMD>lua require('close_buffers').delete({type = 'this'})<CR>]],
        { noremap = true, silent = true }
      )
    end,
  },
}
