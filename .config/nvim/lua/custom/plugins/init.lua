return {
  -- amongst your other plugins
  {
    'akinsho/toggleterm.nvim',
    version = '*',
    config = function()
      require('toggleterm').setup {
        open_mapping = [[<C-z>]],
        direction = 'float',
      }

      function _G.set_terminal_keymaps()
        local opts = { buffer = 0 }
        vim.keymap.set('t', '<esc>', [[<C-\><C-n>]], opts)
        vim.keymap.set('t', '<C-h>', [[<Cmd>wincmd h<CR>]], opts)
        vim.keymap.set('t', '<C-j>', [[<Cmd>wincmd j<CR>]], opts)
        vim.keymap.set('t', '<C-k>', [[<Cmd>wincmd k<CR>]], opts)
        vim.keymap.set('t', '<C-l>', [[<Cmd>wincmd l<CR>]], opts)
        vim.keymap.set('t', '<C-w>', [[<C-\><C-n><C-w>]], opts)
      end

      vim.cmd 'autocmd! TermOpen term://* lua set_terminal_keymaps()'
    end,
  },
  'mattn/vim-goimports',
  'sindrets/diffview.nvim',
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
        ['--max-time'] = 60,
      }

      vim.g.vrc_auto_format_response_enabled = 1
      vim.g.vrc_show_command = 1
      vim.g.vrc_response_default_content_type = 'application/json'
      vim.g.vrc_auto_format_response_patterns = {
        json = 'jq "."',
        xml = 'tidy -xml -i -',
      }
      vim.g.vrc_trigger = '<Leader><C-o>'
    end,
  },
  'simeji/winresizer',
  'tpope/vim-abolish',
  'thinca/vim-quickrun',
  {
    'stevearc/overseer.nvim',
    opts = {},
  },
  'stefandtw/quickfix-reflector.vim',
  'tmux-plugins/vim-tmux-focus-events',
  'kamykn/spelunker.vim',
  'kamykn/popup-menu.nvim',
  'tpope/vim-surround',
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
      require('window-picker').setup()
    end,
  },
  {
    'ggandor/leap.nvim',
    config = function()
      require('leap').set_default_keymaps()
    end,
  },
  {
    'folke/trouble.nvim',
    requires = 'nvim-tree/nvim-web-devicons',
    config = function()
      require('trouble').setup {
        -- your configuration comes here
        -- or leave it empty to use the default settings
        -- refer to the configuration section below
      }
    end,
  },
  'rebelot/kanagawa.nvim',
  'smartpde/telescope-recent-files',
  'tpope/vim-dispatch',
  'kyoh86/vim-go-coverage',
  {
    'echasnovski/mini.nvim',
    version = '*',
    config = function()
      -- default settings
      require('mini.bufremove').setup {}
      require('mini.doc').setup {}
      require('mini.splitjoin').setup {}
      require('mini.trailspace').setup {}
      require('mini.basics').setup {}
      require('mini.align').setup {}
      require('mini.move').setup {}

      -- custom settings
    end,
  },
  'sentriz/vim-print-debug',
  'chrisbra/unicode.vim',
  {
    'windwp/nvim-autopairs',
    event = 'InsertEnter',
    opts = {}, -- this is equalent to setup({}) function
  },
  'deris/vim-rengbang',
  'mattn/vim-goaddtags',
  {
    'kdheepak/lazygit.nvim',
    -- optional for floating window border decoration
    dependencies = {
      'nvim-lua/plenary.nvim',
    },
    config = function()
      vim.api.nvim_create_user_command('G', 'LazyGit', {})
    end,
  },
  {
    'mhartington/formatter.nvim',
    version = '*',
    config = function()
      -- Utilities for creating configurations
      local util = require 'formatter.util'
      -- Provides the Format, FormatWrite, FormatLock, and FormatWriteLock commands
      require('formatter').setup {
        filetype = {
          -- Formatter configurations for filetype "lua" go here
          -- and will be executed in order
          lua = {
            require('formatter.filetypes.lua').stylua,
          },
          python = {
            require('formatter.filetypes.python').black,
            require('formatter.filetypes.python').isort,
          },

          -- Use the special "*" filetype for defining formatter configurations on
          -- any filetype
          ['*'] = {
            -- "formatter.filetypes.any" defines default configurations for any
            -- filetype
            require('formatter.filetypes.any').remove_trailing_whitespace,
          },
        },
      }
      vim.api.nvim_create_autocmd({ 'BufWritePost' }, {
        command = 'FormatWrite',
      })
    end,
  },
  'jbyuki/venn.nvim',
  {
    'zbirenbaum/copilot.lua',
    cmd = 'Copilot',
    event = 'InsertEnter',
    config = function()
      require('copilot').setup {
        suggestion = { enabled = false },
        panel = { enabled = false },
      }
    end,
  },
  {
    'zbirenbaum/copilot-cmp',
    config = function()
      require('copilot_cmp').setup()
    end,
  },
  {
    'f-person/git-blame.nvim',
    config = function()
      require('gitblame').setup {
        --Note how the `gitblame_` prefix is omitted in `setup`
        enabled = false,
      }
    end,
  },
}
