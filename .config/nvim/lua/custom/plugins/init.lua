return {
  'mattn/vim-goimports',
  {
    'kana/vim-operator-replace',
    dependencies = {
      'kana/vim-operator-user',
    },
  },
  'christoomey/vim-tmux-navigator',
  'dhruvasagar/vim-table-mode',
  {
    'diepm/vim-rest-console',
    config = function()
      vim.g.vrc_curl_opts = {
        ['-b'] = '/tmp/cookie.txt',
        ['-c'] = '/tmp/cookie.txt',
        ['-L'] = '',
        ['-i'] = '',
        ['--max-time'] = 60
      }

      vim.g.vrc_auto_format_response_enabled = 1
      vim.g.vrc_show_command = 1
      vim.g.vrc_response_default_content_type = 'application/json'
      vim.g.vrc_auto_format_response_patterns = {
        json = 'jq \".\"',
        xml = 'tidy -xml -i -'
      }
      vim.g.vrc_trigger = '<Leader><C-o>'
    end
  },
  'simeji/winresizer',
  'tpope/vim-abolish',
  'thinca/vim-quickrun',
  'stefandtw/quickfix-reflector.vim',
  'rhysd/vim-go-impl',
  'tmux-plugins/vim-tmux-focus-events',
  'kamykn/spelunker.vim',
  'kamykn/popup-menu.nvim',
  'machakann/vim-sandwich',
  'vim-jp/vimdoc-ja',
  {
    'tyru/operator-camelize.vim',
    dependencies = {
      'kana/vim-operator-user',
    },
  },
  {
    's1n7ax/nvim-window-picker',
    name = 'window-picker',
    event = 'VeryLazy',
    version = '2.*',
    config = function()
      require 'window-picker'.setup()
    end,
  },
  {
    "ggandor/leap.nvim",
    config = function() require("leap").set_default_keymaps() end
  },
  {
    "folke/trouble.nvim",
    requires = "nvim-tree/nvim-web-devicons",
    config = function()
      require("trouble").setup {
        -- your configuration comes here
        -- or leave it empty to use the default settings
        -- refer to the configuration section below
      }
    end
  },
  'rebelot/kanagawa.nvim',
  "smartpde/telescope-recent-files",
  'tpope/vim-dispatch',
  'kyoh86/vim-go-coverage',
  {
    'echasnovski/mini.nvim',
    version = '*',
    config = function()
      -- default settings
      require('mini.bufremove').setup({})
      require('mini.doc').setup({})
      require('mini.splitjoin').setup({})
      require('mini.trailspace').setup({})
      require('mini.basics').setup({})
      require('mini.align').setup({})
      require('mini.move').setup({})

      -- custom settings
    end
  },
  'sentriz/vim-print-debug',
  'chrisbra/unicode.vim',
  {
    'windwp/nvim-autopairs',
    event = "InsertEnter",
    opts = {} -- this is equalent to setup({}) function
  },
  'deris/vim-rengbang',
  'mattn/vim-goaddtags',
}
