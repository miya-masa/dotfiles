return {
  {
    'akinsho/toggleterm.nvim',
    version = '*',
    config = function()
      require('toggleterm').setup {
        open_mapping = [[<C-z>]],
        direction = 'horizontal',
      }

      function _G.set_terminal_keymaps()
        local opts = { buffer = 0 }

        local filetype = vim.bo.filetype
        if filetype ~= 'lazygit' then
          vim.keymap.set('t', '<esc>', [[<C-\><C-n>]], opts)
        end
        vim.keymap.set('t', '<C-h>', [[<Cmd>wincmd h<CR>]], opts)
        vim.keymap.set('t', '<C-j>', [[<Cmd>wincmd j<CR>]], opts)
        vim.keymap.set('t', '<C-k>', [[<Cmd>wincmd k<CR>]], opts)
        vim.keymap.set('t', '<C-l>', [[<Cmd>wincmd l<CR>]], opts)
        vim.keymap.set('t', '<C-w>', [[<C-\><C-n><C-w>]], opts)
      end

      vim.cmd 'autocmd! TermOpen term://* lua set_terminal_keymaps()'
    end,
  },
  'sindrets/diffview.nvim',
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
  {
    'stevearc/overseer.nvim',
    opts = {},
  },
  'stefandtw/quickfix-reflector.vim',
  'tmux-plugins/vim-tmux-focus-events',
  'vim-jp/vimdoc-ja',
  {
    'johmsalas/text-case.nvim',
    dependencies = { 'nvim-telescope/telescope.nvim' },
    config = function()
      require('textcase').setup {}
      require('telescope').load_extension 'textcase'
    end,
    keys = {
      'ga', -- Default invocation prefix
      { 'ga.', '<cmd>TextCaseOpenTelescope<CR>', mode = { 'n', 'x' }, desc = 'Telescope' },
    },
    cmd = {
      -- NOTE: The Subs command name can be customized via the option "substitute_command_name"
      'Subs',
      'TextCaseOpenTelescope',
      'TextCaseOpenTelescopeQuickChange',
      'TextCaseOpenTelescopeLSPChange',
      'TextCaseStartReplacingCommand',
    },
    -- If you want to use the interactive feature of the `Subs` command right away, text-case.nvim
    -- has to be loaded on startup. Otherwise, the interactive feature of the `Subs` will only be
    -- available after the first executing of it or after a keymap of text-case.nvim has been used.
    lazy = false,
  },
  {
    'ggandor/leap.nvim',
    config = function()
      require('leap').set_default_keymaps()
    end,
  },
  {
    'folke/trouble.nvim',
    dependencies = {
      'nvim-tree/nvim-web-devicons',
    },
    config = function()
      require('trouble').setup {
        -- your configuration comes here
        -- or leave it empty to use the default settings
        -- refer to the configuration section below
      }
    end,
  },
  'kyoh86/vim-go-coverage',
  'smartpde/telescope-recent-files',
  'sentriz/vim-print-debug',
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
      if vim.fn.executable 'nvr' == 1 then
        vim.env.GIT_EDITOR = "nvr -cc split --remote-wait +'set bufhidden=wipe'"
      end
      vim.g.lazygit_floating_window_scaling_factor = 0.97

      -- Lazygit起動時にESCを無効化する
      vim.api.nvim_create_augroup('LazygitKeyMapping', {})
      vim.api.nvim_create_autocmd('TermOpen', {
        group = 'LazygitKeyMapping',
        pattern = '*',
        callback = function()
          local filetype = vim.bo.filetype
          if filetype == 'lazygit' then
            vim.api.nvim_buf_set_keymap(0, 't', '<ESC>', '<ESC>', { noremap = true, silent = true })
          end
        end,
      })
    end,
  },
  {
    'jbyuki/venn.nvim',
    config = function()
      -- A機能をトグルする関数を定義
      local function toggle_venn_feature()
        -- バッファローカル変数 'a_feature_enabled' の現在の値を取得
        -- 存在しない場合はデフォルトでfalseを設定
        local is_enabled = vim.b.venn or {}
        is_enabled.feature_enabled = is_enabled.feature_enabled or false

        -- トグル操作
        if is_enabled.feature_enabled then
          -- A機能が有効な場合は無効にする
          vim.cmd [[setlocal ve=]]
          vim.cmd [[mapclear <buffer>]]
          is_enabled.feature_enabled = false
          print 'venn off'
        else
          -- A機能が無効な場合は有効にする
          vim.cmd [[setlocal ve=all]]
          -- draw a line on HJKL keystrokes
          -- draw a box by pressing "f" with visual selection
          vim.api.nvim_buf_set_keymap(0, 'v', '<CR>', ':VBox<CR>', { noremap = true })
          is_enabled.feature_enabled = true
          print 'venn on'
        end
      end

      -- 'AToggle' という名前のコマンドを作成して、上記の関数を割り当てる
      vim.api.nvim_create_user_command('ToggleVenn', toggle_venn_feature, { desc = 'Toggle Venn feature' })
    end,
  },
  {
    'CopilotC-Nvim/CopilotChat.nvim',
    branch = 'canary',
    dependencies = {
      { 'zbirenbaum/copilot.lua' }, -- or github/copilot.vim
      { 'nvim-lua/plenary.nvim' }, -- for curl, log wrapper
    },
    config = function(_, opts)
      local chat = require 'CopilotChat'
      local select = require 'CopilotChat.select'
      opts.prompts = {
        Explain = {
          prompt = '/COPILOT_EXPLAIN 上記のコードの説明をテキストの段落として記述してください。',
        },
        Tests = {
          prompt = '/COPILOT_TESTS 上記のコードに対して一連の詳細な単体テスト関数をテーブルテスト形式で作成してください。',
        },
        GoTests = {
          prompt = '/COPILOT_GO_TESTS 上記のコードに対して一連の詳細な単体テスト関数をテーブルテスト形式で作成してください。アサーションは `github.com/stretchr/testify` を使用してください。モックは使用しません。',
        },
        TestsWithMock = {
          prompt = '/COPILOT_TESTS_WITH_MOCK 上記のコードに対して一連の詳細な単体テスト関数をテーブルテスト形式で作成してください。',
        },
        GoTestsWithMock = {
          prompt = '/COPILOT_GO_TESTS_WITH_MOCK 上記のコードに対して一連の詳細な単体テスト関数をテーブルテスト形式で作成してください。アサーションは `github.com/stretchr/testify` を使用してください。必要に応じてモックライブラリとして `go.uber.org/mock/gomock` を使用してください。',
        },
        GoBench = {
          prompt = '/COPILOT_GO_Bench 上記のコードに対して一連のベンチマークテストを作成してください。',
        },
        Fix = {
          prompt = '/COPILOT_FIX このコードには問題があります。バグが修正された状態で表示されるようにコードを書き換えてください。',
        },
        Optimize = {
          prompt = '/COPILOT_REFACTOR 選択したコードを最適化して、パフォーマンスと可読性を向上させてください。',
        },
        Docs = {
          prompt = '/COPILOT_REFACTOR 選択したコードのドキュメントを作成してください。返信は、元のコードとコメントとして追加されたドキュメントを含むコードブロックである必要があります。使用するプログラミング言語に最も適切なドキュメント スタイルを使用します (例: JavaScript の場合は JSDoc、Python の場合は docstrings など)。',
        },
        FixDiagnostic = {
          prompt = 'ファイル内の次の診断問題にご協力ください。:',
          selection = select.diagnostics,
        },
        Commit = {
          prompt = 'commitize の規則に従って、変更に対するコミットメッセージを記述してください。タイトルは最大 50 文字で、メッセージは 72 文字で折り返されるようにしてください。メッセージ全体を gitcommit 言語のコード ブロックでラップします。',
          selection = select.gitdiff,
        },
        CommitStaged = {
          prompt = 'commitize の規則に従って、変更に対するコミットメッセージを記述してください。タイトルは最大 50 文字で、メッセージは 72 文字で折り返されるようにしてください。メッセージ全体を gitcommit 言語のコード ブロックでラップします。',
          selection = function(source)
            return select.gitdiff(source, true)
          end,
        },
        ExtractMethod = {
          prompt = '選択したコードをメソッドに抽出してください。',
        },
      }
      chat.setup(opts)
    end,
    -- opts = {
    --   -- debug = true, -- Enable debugging
    --   -- See Configuration section for rest
    --   --
    --   -- prompts
    -- },
    -- See Commands section for default commands if you want to lazy load on them
  },
  {
    'jackMort/ChatGPT.nvim',
    event = 'VeryLazy',
    config = function()
      require('chatgpt').setup {
        openai_params = {
          model = 'gpt-4o-2024-05-13',
          frequency_penalty = 0,
          presence_penalty = 0,
          max_tokens = 300,
          temperature = 0,
          top_p = 1,
          n = 1,
        },
        openai_edit_params = {
          model = 'gpt-4o-2024-05-13',
          frequency_penalty = 0,
          presence_penalty = 0,
          temperature = 0,
          top_p = 1,
          n = 1,
        },
      }
    end,
    dependencies = {
      'MunifTanjim/nui.nvim',
      'nvim-lua/plenary.nvim',
      'folke/trouble.nvim',
      'nvim-telescope/telescope.nvim',
    },
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
  {
    'RaafatTurki/hex.nvim',
    config = function()
      require('hex').setup()
    end,
  },
  {
    'chrisgrieser/nvim-spider',
    lazy = true,
    {
      'chrisgrieser/nvim-spider',
      keys = {
        {
          'e',
          "<cmd>lua require('spider').motion('e')<CR>",
          mode = { 'n', 'o', 'x' },
        },
        {
          'w',
          "<cmd>lua require('spider').motion('w')<CR>",
          mode = { 'n', 'o', 'x' },
        },
        {
          'b',
          "<cmd>lua require('spider').motion('b')<CR>",
          mode = { 'n', 'o', 'x' },
        },
      },
    },
  },
  'tpope/vim-dispatch',
}
