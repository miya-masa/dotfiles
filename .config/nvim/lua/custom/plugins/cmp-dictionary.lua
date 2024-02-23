return {
  'uga-rosa/cmp-dictionary',
  config = function()
    require('cmp').setup {
      -- other settings
      sources = {
        -- other sources
        {
          name = 'dictionary',
          keyword_length = 2,
        },
      },
    }
    local dict = require 'cmp_dictionary'
    dict.setup {
      dic = {
        ['*'] = '/usr/share/dict/words',
      },
      -- The following are default values.
      exact_length = 2,
      first_case_insensitive = false,
      document = false,
      document_command = 'wn %s -over',
      sqlite = false,
      max_number_items = -1,
      debug = false,
    }

    -- dict.switcher({
    --   filetype = {
    --     lua = "/path/to/lua.dict",
    --     javascript = { "/path/to/js.dict", "/path/to/js2.dict" },
    --   },
    --   filepath = {
    --     [".*xmake.lua"] = { "/path/to/xmake.dict", "/path/to/lua.dict" },
    --     ["%.tmux.*%.conf"] = { "/path/to/js.dict", "/path/to/js2.dict" },
    --   },
    --   spelllang = {
    --     en = "/path/to/english.dict",
    --   },
    -- })
  end,
}
