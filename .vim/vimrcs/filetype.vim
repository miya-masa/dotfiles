" LSP {{{
augroup Lsp
  autocmd!
  autocmd CursorHold * silent call CocActionAsync('highlight')
augroup END
nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
nmap <silent> gm <Plug>(coc-implementation)
nmap <silent> gr <Plug>(coc-references)
nmap <silent> <Leader>gd <Plug>(coc-definition)
nmap <silent> <Leader>gn <Plug>(coc-declaration)
nmap <silent> <F2> <Plug>(coc-rename)
" Use `[j` and `]j` to navigate diagnostics
nmap <silent> [j <Plug>(coc-diagnostic-prev)
nmap <silent> ]j <Plug>(coc-diagnostic-next)

xmap if <Plug>(coc-funcobj-i)
omap if <Plug>(coc-funcobj-i)
xmap af <Plug>(coc-funcobj-a)
omap af <Plug>(coc-funcobj-a)
xmap ic <Plug>(coc-classobj-i)
omap ic <Plug>(coc-classobj-i)
xmap ac <Plug>(coc-classobj-a)
omap ac <Plug>(coc-classobj-a)
" }}}

" Golang {{{
augroup go
  autocmd!
  autocmd BufWritePre *.go :Autoformat
  autocmd FileType go nnoremap <Leader><C-F> :Autoformat<CR>
  autocmd FileType go command! -nargs=0 GoTagsAdd :CocCommand go.tags.add
  autocmd FileType go command! -nargs=0 GoTagsAddPrompt :CocCommand go.tags.add.prompt
  autocmd FileType go command! -nargs=0 GoInstallGopls :CocCommand go.install.gopls
  autocmd FileType go command! -nargs=0 GoGenerate :Dispatch! go generate %:p:h
  autocmd FileType go command! -nargs=0 GoGenerateTest :CocCommand go.test.generate.exported
  autocmd FileType go command! -nargs=0 GoImpl :CocCommand go.impl.cursor

  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4

  " :GoTest
  autocmd FileType go nnoremap ]] /^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap [[ ?^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap <leader>gt :TestFile<CR>
  " :GoCoverageToggle
  " autocmd FileType go nnoremap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoTestFunc
  autocmd FileType go nnoremap <Leader>gf :TestNearest<CR>
  autocmd FileType go nnoremap <Leader>gs :FillStruct<CR>
  autocmd FileType go nnoremap <Leader>gb :GoBuild<CR>
  autocmd Filetype go command! GoRunArgs :Dispatch go run <arg> %
  autocmd Filetype go command! GoRun :Dispatch go run %
  autocmd Filetype go command! GoBuild :Dispatch go build %:p:h

" GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
  autocmd FileType go nnoremap <silent> <Leader>sj :SplitjoinJoin <CR>
  autocmd FileType go nnoremap <silent> <Leader>ss :SplitjoinSplit <CR>
augroup END
" }}}
" JSON {{{
  augroup json
    autocmd!
    autocmd FileType json syntax match Comment +\/\/.\+$+
  augroup END
" }}}
" Javascript {{{
augroup Javascript
  autocmd!
  autocmd FileType javascript let b:javascript_lib_use_underscore = 1
  autocmd FileType javascript let b:javascript_lib_use_react = 1
augroup END
" }}}
" Python {{{
augroup python
  autocmd!
  autocmd Filetype python map <C-F> :call yapf#YAPF()<cr>
  autocmd Filetype python imap <C-F> <c-o>:call yapf#YAPF()<cr>
augroup END
" }}}
" Vim script {{{
augroup vimscript
  autocmd!
  autocmd Filetype vim setlocal foldmethod=marker
  autocmd Filetype vim setlocal foldmarker={{{,}}}
augroup END
" }}}
" Yaml {{{
augroup yaml
  autocmd!
  autocmd Filetype yaml setlocal foldmethod=indent
augroup END
" }}}
