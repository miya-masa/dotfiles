local hop = require('hop')
-- you can configure Hop the way you like here; see :h hop-config
hop.setup { keys = 'etovxqpdygfblzhckisuran' }
-- place this in one of your configuration file(s)
-- local directions = require('hop.hint').HintDirection
-- vim.keymap.set('', 'f', function() hop.hint_char1({ direction = directions.AFTER_CURSOR, current_line_only = true }) end
--   , { remap = true })
-- vim.keymap.set('', 'F', function() hop.hint_char1({ direction = directions.BEFORE_CURSOR, current_line_only = true }) end
--   , { remap = true })
-- vim.keymap.set('', 't',
--   function() hop.hint_char1({ direction = directions.AFTER_CURSOR, current_line_only = true, hint_offset = -1 }) end,
--   { remap = true })
-- vim.keymap.set('', 'T',
--   function() hop.hint_char1({ direction = directions.BEFORE_CURSOR, current_line_only = true, hint_offset = 1 }) end,
--   { remap = true })
vim.keymap.set('', '<Leader><Leader>w', function() hop.hint_words() end)
vim.keymap.set('', '<Leader><Leader>c', function() hop.hint_char1() end)
vim.keymap.set('', '<Leader><Leader>d', function() hop.hint_char2() end)
vim.keymap.set('', '<Leader><Leader>l', function() hop.hint_lines() end)
