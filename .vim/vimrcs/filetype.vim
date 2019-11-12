" Golang {{{
  augroup go
    autocmd!
    " Show by default 4 spaces for a tab
    autocmd BufNewFile,BufRead FileType go setlocal noexpandtab tabstop=4 shiftwidth=4
    autocmd BufRead $GOPATH/src/*.go
          \  let s:tmp = matchlist(expand('%:p'),
          \  $GOPATH.'/src/\([^/]\+/[^/]\+/[^/]\+/\)')
          \| if len(s:tmp) > 1 |  exe 'silent :GoGuruScope ' . s:tmp[1] . '... -' . s:tmp[1] . 'vendor/...' | endif
          \| unlet s:tmp

    " :GoBuild and :GoTestCompile
    autocmd FileType go nmap <leader>gb :<C-u>call <SID>build_go_files()<CR>
    " :GoTest
    autocmd FileType go nmap <leader>gt  <Plug>(go-test)
    " :GoCoverageToggle
    autocmd FileType go nmap <Leader>gc <Plug>(go-coverage-toggle)
    " :GoDef but opens in a vertical split
    autocmd FileType go nmap <Leader>g- <Plug>(go-def-vertical)
    autocmd FileType go nmap <Leader>g<S-\> <Plug>(go-def-split)
    " :GoTestFunc
    autocmd FileType go nmap <Leader>gf <Plug>(go-test-func)
    autocmd FileType go nnoremap <Leader>gs :GoFillStruct<CR>
    autocmd FileType go nnoremap <Leader>g<C-g> :GoDeclsDir<CR>
    autocmd FileType go nnoremap <Leader>ge :GoIfErr<CR>

    " :GoAlternate  commands :A, :AV, :AS and :AT
    autocmd Filetype go command! -bang A call go#alternate#Switch(<bang>0, 'edit')
    autocmd Filetype go command! -bang AV call go#alternate#Switch(<bang>0, 'vsplit')
    autocmd Filetype go command! -bang AS call go#alternate#Switch(<bang>0, 'split')
    autocmd Filetype go command! -bang AT call go#alternate#Switch(<bang>0, 'tabe')
    autocmd Filetype go command! GoRunArgs :!go run % <args>

  " GoKeyword
    autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
    autocmd FileType go nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
    autocmd FileType go nmap <silent> <Leader>gd <Plug>(coc-definition)
    autocmd FileType go nmap <silent> <Leader>gn <Plug>(coc-declaration)
    autocmd FileType go nmap <silent> <Leader>gr <Plug>(coc-rename)
    autocmd FileType go nmap <Leader>im :GoImport
  augroup END
  " build_go_files is a custom function that builds or compiles the test file.
  " It calls :GoBuild if its a Go file, or :GoTestCompile if it's a test file
  function! s:build_go_files()
    let l:file = expand('%')
    if l:file =~# '^\f\+_test\.go$'
      call go#test#Test(0, 1)
    elseif l:file =~# '^\f\+\.go$'
      call go#cmd#Build(0)
    endif
  endfunction
" }}}
"
" Java {{{
  augroup java
    autocmd!
    autocmd FileType java nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
    autocmd FileType java nmap <silent> <Leader>gd <Plug>(coc-definition)
    autocmd FileType java nmap <silent> <Leader>gn <Plug>(coc-declaration)
    autocmd FileType java nmap <silent> <Leader>gr <Plug>(coc-rename)
  augroup END
" }}}
" JSON {{{
  augroup json
    autocmd!
    autocmd FileType json syntax match Comment +\/\/.\+$+
  augroup END
" }}}
" PlantUML {{{
augroup PlantUML
  autocmd!
  au FileType plantuml command! OpenUml :!open -a Google\ Chrome %
augroup END
" }}}
"
" Javascript {{{
augroup Javascript
  autocmd!
  autocmd FileType javascript let b:javascript_lib_use_underscore = 1
  autocmd FileType javascript let b:javascript_lib_use_react = 1
augroup END
" }}}
"
" Python {{{
augroup python
  autocmd!
  autocmd Filetype python map <C-F> :call yapf#YAPF()<cr>
  autocmd Filetype python imap <C-F> <c-o>:call yapf#YAPF()<cr>
augroup END
" }}}
