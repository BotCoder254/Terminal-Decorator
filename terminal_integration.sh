#!/bin/bash

# Terminal Decorator Bash Integration
# This script provides integration with the Python terminal decorator

# ANSI Color Codes
declare -A colors=(
    ["black"]="0" ["red"]="1" ["green"]="2" ["yellow"]="3"
    ["blue"]="4" ["magenta"]="5" ["cyan"]="6" ["white"]="7"
    ["bright_black"]="90" ["bright_red"]="91" ["bright_green"]="92"
    ["bright_yellow"]="93" ["bright_blue"]="94" ["bright_magenta"]="95"
    ["bright_cyan"]="96" ["bright_white"]="97"
)

# Unicode Symbols
declare -A symbols=(
    ["check"]="✓" ["cross"]="✗" ["arrow"]="➜" ["star"]="★"
    ["heart"]="❤" ["info"]="ℹ" ["warning"]="⚠" ["error"]="✗"
    ["cpu"]="🔲" ["memory"]="📊" ["disk"]="💾" ["network"]="🌐"
    ["clock"]="🕐" ["user"]="👤" ["host"]="🖥" ["temp"]="🌡"
)

# Terminal Utilities
TERM_COLS=$(tput cols)
TERM_LINES=$(tput lines)
METRICS_UPDATE_INTERVAL=2  # seconds

# Color Functions
term_color() {
    local fg_color=$1
    local bg_color=$2
    local style=$3
    
    # Convert color names to codes
    local fg_code=${colors[$fg_color]:-"0"}  # Default to black if color not found
    local bg_code=""
    
    # Only process background color if provided
    if [[ -n $bg_color ]]; then
        bg_code=";${colors[$bg_color]:-"0"}"
    fi
    
    # Style codes: 0=normal, 1=bold, 2=dim, 3=italic, 4=underline
    [[ -z $style ]] && style=0
    
    if [[ -n $bg_code ]]; then
        echo -e "\e[${style};${fg_code}${bg_code}m"
    else
        echo -e "\e[${style};${fg_code}m"
    fi
}

reset_color() {
    echo -e "\e[0m"
}

# System Metrics Functions
get_cpu_usage() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    echo "${cpu_usage%.*}"
}

get_memory_usage() {
    local total=$(free -m | awk '/Mem:/ {print $2}')
    local used=$(free -m | awk '/Mem:/ {print $3}')
    local percentage=$((used * 100 / total))
    echo "$percentage"
}

get_disk_usage() {
    local usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    echo "$usage"
}

get_network_stats() {
    local interface=$(ip route | awk '/default/ {print $5}' | head -n1)
    local rx_bytes=$(cat /sys/class/net/$interface/statistics/rx_bytes)
    local tx_bytes=$(cat /sys/class/net/$interface/statistics/tx_bytes)
    echo "$rx_bytes $tx_bytes"
}

get_system_load() {
    local load=$(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1)
    echo "${load## }"
}

# Styling Functions
print_banner() {
    local text="$1"
    local color="${2:-bright_cyan}"
    local padding=$(( (TERM_COLS - ${#text}) / 2 ))
    
    echo
    printf "%${padding}s" ""
    echo -e "$(term_color $color)$text$(reset_color)"
    echo
}

print_status() {
    local message="$1"
    local status="$2"
    local color="bright_green"
    local symbol=${symbols["check"]}
    
    case $status in
        "error")
            color="bright_red"
            symbol=${symbols["error"]}
            ;;
        "warning")
            color="bright_yellow"
            symbol=${symbols["warning"]}
            ;;
        "info")
            color="bright_blue"
            symbol=${symbols["info"]}
            ;;
    esac
    
    echo -e "$(term_color $color)$symbol $(reset_color)$message"
}

draw_line() {
    local char="${1:-─}"
    printf "%${TERM_COLS}s" | tr " " "$char"
    echo
}

# Progress Bar Functions
draw_progress_bar() {
    local value=$1
    local max_value=${2:-100}
    local width=${3:-50}
    local title="$4"
    
    local percentage=$((value * 100 / max_value))
    local filled=$((percentage * width / 100))
    local empty=$((width - filled))
    local color="bright_green"
    
    [[ $percentage -gt 80 ]] && color="bright_red"
    [[ $percentage -gt 60 && $percentage -le 80 ]] && color="bright_yellow"
    
    printf "%-15s [" "$title"
    echo -ne "$(term_color $color)"
    printf "%${filled}s" | tr " " "█"
    echo -ne "$(reset_color)"
    printf "%${empty}s" | tr " " "░"
    printf "] %3d%%\n" "$percentage"
}

# System Metrics Display
show_system_metrics() {
    local cpu_usage=$(get_cpu_usage)
    local memory_usage=$(get_memory_usage)
    local disk_usage=$(get_disk_usage)
    local load=$(get_system_load)
    
    clear
    print_banner "System Metrics" "bright_magenta"
    echo -e "$(term_color bright_blue)${symbols["host"]} $(hostname) - $(date '+%Y-%m-%d %H:%M:%S')$(reset_color)"
    draw_line
    
    echo -e "\n$(term_color bright_cyan)System Resources:$(reset_color)"
    draw_progress_bar "$cpu_usage" 100 30 "CPU"
    draw_progress_bar "$memory_usage" 100 30 "Memory"
    draw_progress_bar "$disk_usage" 100 30 "Disk"
    
    echo -e "\n$(term_color bright_cyan)System Load:$(reset_color) $load"
    
    # Network stats
    read rx_bytes tx_bytes <<< $(get_network_stats)
    echo -e "\n$(term_color bright_cyan)Network (${symbols["network"]}):$(reset_color)"
    echo "↓ RX: $(numfmt --to=iec-i --suffix=B $rx_bytes)"
    echo "↑ TX: $(numfmt --to=iec-i --suffix=B $tx_bytes)"
    
    draw_line
}

# Git Integration with Enhanced Display
git_prompt() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local branch=$(git symbolic-ref --short HEAD 2>/dev/null)
        local status=""
        local color="bright_green"
        
        if [[ -n $(git status -s 2>/dev/null) ]]; then
            status="*"
            color="bright_yellow"
        fi
        
        if [[ -n $(git log --branches --not --remotes 2>/dev/null) ]]; then
            status="${status}↑"
        fi
        
        echo -e "$(term_color $color)${symbols["arrow"]} ($branch$status)$(reset_color)"
    fi
}

# Custom Prompt with Enhanced Features
set_custom_prompt() {
    local user_color="bright_cyan"
    local path_color="bright_blue"
    local git_info=$(git_prompt)
    
    PS1="\[$(term_color $user_color)\]${symbols["user"]} \u\[$(reset_color)\] at "
    PS1+="\[$(term_color $path_color)\]\w\[$(reset_color)\] "
    PS1+="$git_info"
    PS1+="\n${symbols["arrow"]} "
    
    export PS1
}

# System Information with Enhanced Display
show_system_info() {
    local os=$(uname -s)
    local kernel=$(uname -r)
    local hostname=$(hostname)
    local uptime=$(uptime -p)
    
    print_banner "System Information" "bright_magenta"
    print_status "OS: $os ($kernel)" "info"
    print_status "Host: $hostname" "info"
    print_status "Uptime: $uptime" "info"
    print_status "Shell: $SHELL" "info"
    print_status "Terminal: $TERM" "info"
    draw_line
}

# Initialize Terminal
init_terminal() {
    # Set custom prompt
    set_custom_prompt
    
    # Terminal title
    echo -ne "\033]0;Terminal Pro\007"
    
    # Welcome message
    show_system_metrics
    show_system_info
    
    # Start metrics update in background
    while true; do
        sleep $METRICS_UPDATE_INTERVAL
        show_system_metrics
    done &
}

# Execute initialization if script is sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    init_terminal
fi 