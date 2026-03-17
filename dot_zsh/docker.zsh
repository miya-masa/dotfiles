# dk - fzf-powered Docker operations
#
# Usage: dk
#   Single entry point for all Docker operations via fzf.
#   All executed commands are recorded in zsh history (Ctrl+R to reuse).

# __dk_run: コマンド実行 + zsh履歴記録
# eval ではなく直接実行。引数境界が保持されるため sh -c '...' 等が安全に動作する。
__dk_run() {
  print -s "$*"
  "$@"
}

# __dk_has_compose: composeファイルの存在チェック
__dk_has_compose() {
  docker compose config --services &>/dev/null
}

# __dk_select_container: 稼働中コンテナをfzfで選択
# Usage: __dk_select_container [--multi]
# Returns: 選択されたコンテナID（複数選択時は改行区切り）
__dk_select_container() {
  local multi_flag=""
  [[ "$1" == "--multi" ]] && multi_flag="--multi"

  local ps_output
  ps_output=$(docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}')

  local count
  count=$(echo "$ps_output" | tail -n +2 | grep -c .)

  if [[ "$count" -eq 0 ]]; then
    echo "No running containers." >&2
    return 1
  fi

  echo "$ps_output" | fzf --header-lines=1 $multi_flag \
    --prompt 'container> ' \
    --preview 'docker inspect --format "Name:    {{.Name}}
Image:   {{.Config.Image}}
Status:  {{.State.Status}}
Started: {{.State.StartedAt}}
Ports:   {{range \$p, \$conf := .NetworkSettings.Ports}}{{\$p}} {{end}}" {1}' \
    | awk '{print $1}'
}

# __dk_select_service: composeサービスをfzfで選択
# Usage: __dk_select_service [--multi]
# Returns: 選択されたサービス名（複数選択時は改行区切り）
__dk_select_service() {
  local multi_flag=""
  [[ "$1" == "--multi" ]] && multi_flag="--multi"

  local services
  services=$(docker compose config --services 2>/dev/null)

  if [[ -z "$services" ]]; then
    echo "No compose services found." >&2
    return 1
  fi

  echo "$services" | fzf $multi_flag --prompt 'compose> '
}

# dk: メインエントリポイント
dk() {
  local actions="logs
exec
stop
restart
kill-all
stats
images"

  # composeファイルがあればcompose系アクションを追加
  if __dk_has_compose; then
    actions="$actions
compose-logs
compose-restart
compose-up
compose-down"
  fi

  # ctop が使えれば追加
  if command -v ctop &>/dev/null; then
    actions="$actions
ctop"
  fi

  local action
  action=$(echo "$actions" | fzf --prompt 'docker> ') || return

  case "$action" in
    logs)
      local id
      id=$(__dk_select_container) || return
      __dk_run docker logs -f "$id"
      ;;
    exec)
      local id
      id=$(__dk_select_container) || return
      # exec は sh -c '...' の引用符を履歴に正しく残すため __dk_run を使わず直接処理
      print -s "docker exec -it $id sh -c 'command -v bash > /dev/null 2>&1 && exec bash || exec sh'"
      docker exec -it "$id" sh -c 'command -v bash > /dev/null 2>&1 && exec bash || exec sh'
      ;;
    stop)
      local ids
      ids=$(__dk_select_container --multi) || return
      echo "$ids" | while read -r id; do
        __dk_run docker stop "$id"
      done
      ;;
    restart)
      local id
      id=$(__dk_select_container) || return
      __dk_run docker restart "$id"
      ;;
    kill-all)
      local count
      count=$(docker container ls -q | wc -l | tr -d ' ')
      if [[ "$count" -eq 0 ]]; then
        echo "No running containers." >&2
        return
      fi
      printf "Kill all %s containers? [y/N]: " "$count"
      local confirm
      read -r confirm
      if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        # パイプラインは __dk_run (直接実行) では使えないため個別処理
        print -s "docker container ls -q | xargs docker kill"
        docker container ls -q | xargs docker kill
      fi
      ;;
    stats)
      local ids
      ids=$(__dk_select_container --multi) || return
      __dk_run docker stats --no-stream $ids
      ;;
    images)
      __dk_run docker images
      ;;
    compose-logs)
      local svc
      svc=$(__dk_select_service) || return
      __dk_run docker compose logs -f "$svc"
      ;;
    compose-restart)
      local svcs
      svcs=$(__dk_select_service --multi) || return
      __dk_run docker compose restart $svcs
      ;;
    compose-up)
      local svcs
      svcs=$(__dk_select_service --multi) || return
      __dk_run docker compose up -d $svcs
      ;;
    compose-down)
      __dk_run docker compose down
      ;;
    ctop)
      __dk_run ctop
      ;;
  esac
}
