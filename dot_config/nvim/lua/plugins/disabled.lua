-- LazyVim 本体が入れる plugin のうち、AI agent 中心の使い方で出番が無くなった
-- ものを無効化する。extras で外せるものは lazyvim.json 側で外している。
--
-- 判断基準は「手でコードを書く場面がほぼ無い」こと。読む・見る・指摘する側
-- (LSP / picker / diffview / aerial / treesitter) は残している。
-- 困ったらこのファイルの該当行を消せば戻る。
return {
  -- 手書き編集の支援。書かなくなったので出番が無い。
  { "folke/flash.nvim", enabled = false },
  { "MagicDuck/grug-far.nvim", enabled = false },

  -- DB クライアント。SQL の LSP / treesitter (lang.sql) は残し、UI だけ落とす。
  { "tpope/vim-dadbod", enabled = false },
  { "kristijanhusak/vim-dadbod-ui", enabled = false },
  { "kristijanhusak/vim-dadbod-completion", enabled = false },
  {
    -- lang.sql は blink の sources.default へ "dadbod" を足す (LazyVim の
    -- extras/lang/sql.lua)。default に居ると filetype を問わず参照され、
    -- blink は provider を pcall 無しで require する
    -- (blink.cmp/sources/lib/provider/init.lua)。上で dependency を落とした
    -- 結果 vim_dadbod_completion が存在しないので、外さないと全 filetype で
    -- 補完が落ちる。
    "saghen/blink.cmp",
    optional = true,
    opts = function(_, opts)
      local sources = opts.sources or {}
      sources.default = vim.tbl_filter(function(name)
        return name ~= "dadbod"
      end, sources.default or {})
      if sources.providers then
        sources.providers.dadbod = nil
      end
      opts.sources = sources
    end,
  },
}
