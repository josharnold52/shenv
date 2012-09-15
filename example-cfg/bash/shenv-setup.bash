
function shenv(){
  local cmdsToRun
  pushd $SHENV_HOME >/dev/null
  cmdsToRun=`python3 -m shenv.app --shell bash ~/.shenv/shenv_cfg.py '(stdout)' "$@"`
  eval "$cmdsToRun"
  popd >/dev/null
}

function xshenv(){
  local cmdsToRun
  pushd $SHENV_HOME >/dev/null
  python3 -m shenv.app --shell bash ~/.shenv/shenv_cfg.py '(stdout)' "$@"
  popd >/dev/null
}


# export -f shenv
# export -f xshenv

_shenv_completion() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    if (( $COMP_CWORD <= 1 )) ; then
      opts=`shenv | grep 'shenv [a-z]' | cut -f 2 -d ' ' | sort | uniq | tr '\n' ' '`
      COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
      return 0      
    fi
    
    if (( $COMP_CWORD == 2 )) ; then
      if shenv | grep --fixed-strings "${COMP_WORDS[0]} ${COMP_WORDS[1]} "'<cat>' >/dev/null ; then
        opts=`shenv spit | grep -P '\S' | sort | uniq | tr '\n' ' '`
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0      
      fi
    fi

    if (( $COMP_CWORD == 3 )) ; then
      if shenv | grep --fixed-strings "${COMP_WORDS[0]} ${COMP_WORDS[1]} "'<cat> <ver>' >/dev/null ; then
        opts=`shenv spit $prev | grep -P '\S' | sort | uniq | tr '\n' ' '`
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0      
      fi
    fi    
}

complete -F _shenv_completion shenv

