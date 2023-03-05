require('dashboard').setup {
  theme = 'doom',
  config = {
    center = {
      {
        icon = '',
        icon_hl = 'group',
        desc = 'Telekasten goto_today',
        desc_hl = 'group',
        key = '<Leader> z T',
        key_hl = 'group',
        action = 'Telekasten goto_today',
      },
      {
        icon = '',
        desc = 'Recently opened files',
        action = 'Telescope recent_files pick',
        key = '<Leader> <C-;>'
      },
      { icon = '',
        desc = 'Find  File',
        action = 'Telescope find_files find_command=rg,--hidden,--files',
        key = '<Leader> <C-F>'
      },
      { icon = '',
        desc = 'File Browser',
        action = 'NvimTreeOpen',
        key = '-'
      },
      { icon = '',
        desc = 'Find  word',
        action = 'Telescope live_grep',
        key = '<Leader> <C-R>'
      },
    },
    week_header = {
      enable = true,
    }
  }
}
-- db.custom_header = {
--   '',
--   '           __                                                                               __',
--   '  ___ ___ /\\_\\  __  __     __               ___ ___      __      ____     __        __  __ /\\_\\    ___ ___',
--   '/\\\' __` __`\\/\\ \\/\\ \\/\\ \\  /\'__`\\   _______ /\' __` __`\\  /\'__`\\   /\',__\\  /\'__`\\     /\\ \\/\\ \\\\/\\ \\ /\' __` __`\\',
--   '/\\ \\/\\ \\/\\ \\ \\ \\ \\ \\_\\ \\/\\ \\L\\.\\_/\\______\\/\\ \\/\\ \\/\\ \\/\\ \\L\\.\\_/\\__, `\\/\\ \\L\\.\\_   \\ \\ \\_/ |\\ \\ \\/\\ \\/\\ \\/\\ \\',
--   '\\ \\_\\ \\_\\ \\_\\ \\_\\/`____ \\ \\__/.\\_\\/______/\\ \\_\\ \\_\\ \\_\\ \\__/.\\_\\/\\____/\\ \\__/.\\_\\   \\ \\___/  \\ \\_\\ \\_\\ \\_\\ \\_\\',
--   ' \\/_/\\/_/\\/_/\\/_/`/___/> \\/__/\\/_/         \\/_/\\/_/\\/_/\\/__/\\/_/\\/___/  \\/__/\\/_/    \\/__/    \\/_/\\/_/\\/_/\\/_/',
--   '                    /\\___/',
--   '                    \\/__/',
--   '',
--   '',
--   '',
-- }
