return {
  name = 'go generate',
  builder = function()
    local file = vim.fn.expand '%:p'
    local cmd = { 'go', 'generate', file }
    return {
      cmd = cmd,
      components = {
        { 'on_output_quickfix', set_diagnostics = true },
        'on_result_diagnostics',
        'default',
      },
    }
  end,
  condition = {
    filetype = { 'go' },
  },
}
