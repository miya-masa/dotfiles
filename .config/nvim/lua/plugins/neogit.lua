require('neogit').setup {
  integrations = {
    diffview = true
  }
}


-- command! G Neogit
--
vim.api.nvim_create_user_command('G', 'Neogit', {})
