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
