return {
  {
    "nvimtools/none-ls.nvim",
    opts = function(_, opts)
      for i, src in ipairs(opts.sources or {}) do
        if src.name == "markdownlint-cli2" then
          opts.sources[i] = src.with({
            extra_args = { "--config", vim.fn.expand("~/.markdownlint.yaml") },
          })
        end
      end
    end,
  },
}
