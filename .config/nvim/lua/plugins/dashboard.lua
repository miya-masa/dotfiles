local db = require('dashboard')
db.custom_header = {
  '',
  '           __                                                                               __',
  '  ___ ___ /\\_\\  __  __     __               ___ ___      __      ____     __        __  __ /\\_\\    ___ ___',
  '/\\\' __` __`\\/\\ \\/\\ \\/\\ \\  /\'__`\\   _______ /\' __` __`\\  /\'__`\\   /\',__\\  /\'__`\\     /\\ \\/\\ \\\\/\\ \\ /\' __` __`\\',
  '/\\ \\/\\ \\/\\ \\ \\ \\ \\ \\_\\ \\/\\ \\L\\.\\_/\\______\\/\\ \\/\\ \\/\\ \\/\\ \\L\\.\\_/\\__, `\\/\\ \\L\\.\\_   \\ \\ \\_/ |\\ \\ \\/\\ \\/\\ \\/\\ \\',
  '\\ \\_\\ \\_\\ \\_\\ \\_\\/`____ \\ \\__/.\\_\\/______/\\ \\_\\ \\_\\ \\_\\ \\__/.\\_\\/\\____/\\ \\__/.\\_\\   \\ \\___/  \\ \\_\\ \\_\\ \\_\\ \\_\\',
  ' \\/_/\\/_/\\/_/\\/_/`/___/> \\/__/\\/_/         \\/_/\\/_/\\/_/\\/__/\\/_/\\/___/  \\/__/\\/_/    \\/__/    \\/_/\\/_/\\/_/\\/_/',
  '                    /\\___/',
  '                    \\/__/',
  '',
  '',
  '',
}
-- db.custom_center  -- table type and in this table you can set icon,desc,shortcut,action keywords. desc must be exist and type is string
--                   -- icon type is nil or string
--                   -- icon_hl table type { fg ,bg} see `:h vim.api.nvim_set_hl` opts
--                   -- shortcut type is nil or string also like icon
--                   -- action type can be string or function or nil.
--                   -- if you don't need any one of icon shortcut action ,you can ignore it.
-- db.custom_footer  -- type can be nil,table or function(must be return table in function)
-- db.preview_file_Path          -- string or function type that mean in function you can dynamic generate height width
-- db.preview_file_height        -- number type
-- db.preview_file_width         -- number type
-- db.preview_command            -- string type (can be ueberzug which only work in linux)
-- db.confirm_key                -- string type key that do confirm in center select
-- db.hide_statusline            -- boolean default is true.it will hide statusline in dashboard buffer and auto open in other buffer
-- db.hide_tabline               -- boolean default is true.it will hide tabline in dashboard buffer and auto open in other buffer
-- db.hide_winbar                -- boolean default is true.it will hide the winbar in dashboard buffer and auto open in other buffer
-- db.session_directory          -- string type the directory to store the session file
-- db.session_auto_save_on_exit  -- boolean default is false.it will auto-save the current session on neovim exit if a session exists and more than one buffer is loaded
-- db.session_verbose            -- boolean default true.it will display the session file path on SessionSave and SessionLoad
-- db.header_pad                 -- number type default is 1
-- db.center_pad                 -- number type default is 1
-- db.footer_pad                 -- number type default is 1
--
-- -- example of db.custom_center for new lua coder,the value of nil mean if you
-- -- don't need this filed you can not write it
-- db.custom_center = {
--   {icon_hl={fg="color_code"},icon ="some icon",desc="some desc"} --correct
--   { icon = 'some icon' desc = 'some description here' } --correct if you don't action filed
--   { desc = 'some description here' }                    --correct if you don't action and icon filed
--   { desc = 'some description here' action = 'Telescope find files'} --correct if you don't icon filed
-- }
--
-- -- Custom events
-- DBSessionSavePre   -- a custom user autocommand to add functionality before auto-saving the current session on exit
-- DBSessionSaveAfter -- a custom user autocommand to add functionality after auto-saving the current session on exit
--
-- -- Example: Close NvimTree buffer before auto-saving the current session
-- autocmd('User', {
--     pattern = 'DBSessionSavePre',
--     callback = function()
--       pcall(vim.cmd, 'NvimTreeClose')
--     end,
-- })
--
--
-- -- Highlight Group
-- DashboardHeader DashboardCenter DashboardShortCut DashboardFooter
--
-- -- Command
--
-- DashboardNewFile  -- if you like use `enew` to create file,Please use this command,it's wrap enew and restore the statsuline and tabline
-- SessionSave,SessionLoad,SessionDelete
--
--
--
db.custom_center = {
  { icon = '  ',
    desc = 'Telekasten goto_today                      ',
    shortcut = '<Leader> z T',
    action = 'Telekasten goto_today' },
  { icon = '  ',
    desc = 'Recently opened files                   ',
    action = 'Telescope recent_files pick',
    shortcut = '<Leader> <C-;>' },
  { icon = '  ',
    desc = 'Find  File                              ',
    action = 'Telescope find_files find_command=rg,--hidden,--files',
    shortcut = '<Leader> <C-F>' },
  { icon = '  ',
    desc = 'File Browser                                        ',
    action = 'NvimTree',
    shortcut = '-' },
  { icon = '  ',
    desc = 'Find  word                              ',
    action = 'Telescope live_grep',
    shortcut = '<Leader> <C-R>' },
}
