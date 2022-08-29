" Golang {{{
augroup go
  autocmd!
  autocmd FileType go command! -nargs=0 GoGenerate :Dispatch! go generate %:p:h

  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4

  autocmd FileType go nnoremap ]] /^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap [[ ?^func<CR>:nohlsearch<CR>
  function! DebugNearest()
    let g:test#go#runner = 'delve'
    TestNearest
    unlet g:test#go#runner
  endfunction
  autocmd FileType go nmap <silent> t<C-d> :cd %:p:h<cr>:call DebugNearest()<CR>
  function! DebugNearestIntegration()
    let g:test#go#runner = 'delve'
    TestNearest -tags integration
    unlet g:test#go#runner
  endfunction
  autocmd FileType go nmap <silent> ti<C-d> :cd %:p:h<cr>:pwd<cr>:call DebugNearestIntegration()<CR>

" GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
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
" Rust {{{
augroup rust
  autocmd!

" GoKeyword
  autocmd FileType rust set iskeyword=a-z,A-Z,48-57,&,*
  autocmd FileType rust nnoremap <silent> <Leader>sj :SplitjoinJoin <CR>
  autocmd FileType rust nnoremap <silent> <Leader>ss :SplitjoinSplit <CR>

  autocmd BufNewFile,BufRead *.rs let g:quickrun_config.rust = {'exec' : 'cargo run'}

augroup END
" }}}
