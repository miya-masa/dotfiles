" Golang {{{
  augroup go
    autocmd!
    " Show by default 4 spaces for a tab
    autocmd BufNewFile,BufRead FileType go setlocal noexpandtab tabstop=4 shiftwidth=4
    autocmd BufWritePre FileType go :call CocAction('runCommand', 'editor.action.organizeImport')
    autocmd BufRead $GOPATH/src/*.go
          \  let s:tmp = matchlist(expand('%:p'),
          \  $GOPATH.'/src/\([^/]\+/[^/]\+/[^/]\+/\)')
          \| if len(s:tmp) > 1 |  exe 'silent :GoGuruScope ' . s:tmp[1] . '... -' . s:tmp[1] . 'vendor/...' | endif
          \| unlet s:tmp

    " :GoBuild and :GoTestCompile
    autocmd FileType go nmap <leader>gb :<C-u>call <SID>build_go_files()<CR>
    " :GoTest
    autocmd FileType go nmap <leader>gt :TestFile<CR>
    " :GoCoverageToggle
    autocmd FileType go nmap <Leader>gc <Plug>(go-coverage-toggle)
    " :GoTestFunc
    autocmd FileType go nmap <Leader>gf :TestNearest<CR>
    autocmd FileType go nnoremap <Leader>gs :GoFillStruct<CR>
    autocmd FileType go nnoremap <Leader>g<C-g> :GoDeclsDir<CR>
    autocmd FileType go nnoremap <Leader>ge :GoIfErr<CR>

    " :GoAlternate  commands :A, :AV, :AS and :AT
    autocmd Filetype go command! -bang A call s:switch(<bang>0, 'edit')
    autocmd Filetype go command! -bang AV call s:switch(<bang>0, 'vsplit')
    autocmd Filetype go command! -bang AS call s:switch(<bang>0, 'split')
    autocmd Filetype go command! -bang AT call s:switch(<bang>0, 'tabe')
    autocmd Filetype go command! GoRunArgs :!go run % <args>

  " GoKeyword
    autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
    autocmd FileType go nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
    autocmd FileType go nmap <silent> <Leader>gd <Plug>(coc-definition)
    autocmd FileType go nmap <silent> <Leader>gn <Plug>(coc-declaration)
    autocmd FileType go nmap <silent> <Leader>gr <Plug>(coc-rename)
    autocmd FileType go nmap <silent> <Leader><C-F> :GoImports<CR>
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

  function! s:switch(bang, cmd) abort
    let file = expand('%')
    if empty(file)
      echo "no buffer name"
      return
    elseif file =~# '^\f\+_test\.go$'
      let l:root = split(file, '_test.go$')[0]
      let l:alt_file = l:root . ".go"
    elseif file =~# '^\f\+\.go$'
      let l:root = split(file, ".go$")[0]
      let l:alt_file = l:root . '_test.go'
    else
      echo "not a go file"
      return
    endif
    if !filereadable(alt_file) && !bufexists(alt_file) && !a:bang
      echo "couldn't find ".alt_file
      return
    elseif empty(a:cmd)
      execute ":" . go#config#AlternateMode() . " " . alt_file
    else
      execute ":" . a:cmd . " " . alt_file
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
