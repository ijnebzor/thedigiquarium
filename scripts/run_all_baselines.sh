#!/bin/bash
#
# Run All Baselines Script
# Executes baseline assessments for all 17 tanks with validation and retry logic
#
# Usage: ./run_all_baselines.sh [--dry-run] [--verbose] [--timeout SECONDS]
#

set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/tanks"
BASELINE_SCRIPT="$PROJECT_ROOT/src/explorer/baseline.py"
VALIDATOR_SCRIPT="$SCRIPT_DIR/validate_baseline.py"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/baselines}"
REPORT_FILE="$LOG_DIR/baseline_report_$(date +%Y%m%d_%H%M%S).txt"

# Configurable parameters
MAX_RETRIES=3
TIMEOUT=300  # 5 minutes per baseline
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Arrays to track results
declare -a PASS_TANKS
declare -a FAIL_TANKS
declare -a RETRY_TANKS
declare -a SKIPPED_TANKS

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure directories exist
mkdir -p "$LOG_DIR"

# Header
print_header() {
    echo "======================================================================"
    echo "BASELINE ASSESSMENT - ALL TANKS"
    echo "======================================================================"
    echo "Start Time: $(date)"
    echo "Config Dir: $CONFIG_DIR"
    echo "Log Dir: $LOG_DIR"
    echo "Max Retries: $MAX_RETRIES"
    echo "Timeout: ${TIMEOUT}s per baseline"
    if [ "$DRY_RUN" = true ]; then
        echo "Mode: DRY RUN (no actual execution)"
    fi
    echo "======================================================================"
    echo ""
}

# Log function
log() {
    local level=$1
    shift
    local msg="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $msg" | tee -a "$REPORT_FILE"
}

# Verbose logging
vlog() {
    if [ "$VERBOSE" = true ]; then
        log "DEBUG" "$@"
    fi
}

# Extract tank name from YAML config
get_tank_name() {
    local config_file=$1
    grep "^name:" "$config_file" | awk '{print $2}' | tr -d "'"
}

# Extract gender from YAML config
get_tank_gender() {
    local config_file=$1
    grep "^gender:" "$config_file" | awk '{print $2}' | tr -d "'"
}

# Extract tank ID from YAML config
get_tank_id() {
    local config_file=$1
    grep "^tank_id:" "$config_file" | awk '{print $2}' | tr -d "'" | sed 's/tank-[0-9]*-//'
}

# Run a single baseline assessment
run_baseline() {
    local tank_name=$1
    local gender=$2
    local tank_config=$3
    local attempt=$4

    local tank_log_dir="$LOG_DIR/$tank_name"
    mkdir -p "$tank_log_dir"

    local baseline_json="$tank_log_dir/baseline.json"
    local attempt_log="$tank_log_dir/attempt_${attempt}.log"

    vlog "Running baseline for $tank_name (attempt $attempt)"

    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: Would execute baseline for $tank_name" | tee -a "$attempt_log"
        return 0
    fi

    # Set environment variables for baseline script
    export TANK_NAME="$tank_name"
    export GENDER="$gender"
    export LOG_DIR="$tank_log_dir"

    # Run baseline with timeout
    timeout "$TIMEOUT" python3 "$BASELINE_SCRIPT" > "$attempt_log" 2>&1
    local exit_code=$?

    if [ $exit_code -eq 124 ]; then
        log "ERROR" "Baseline for $tank_name timed out (attempt $attempt)"
        return 1
    fi

    if [ $exit_code -ne 0 ]; then
        log "ERROR" "Baseline for $tank_name failed with exit code $exit_code (attempt $attempt)"
        return 1
    fi

    if [ ! -f "$baseline_json" ]; then
        log "ERROR" "Baseline JSON not created for $tank_name (attempt $attempt)"
        return 1
    fi

    return 0
}

# Validate baseline result
validate_baseline() {
    local tank_name=$1
    local tank_config=$2

    local tank_log_dir="$LOG_DIR/$tank_name"
    local baseline_json="$tank_log_dir/baseline.json"
    local validation_log="$tank_log_dir/validation.log"

    vlog "Validating baseline for $tank_name"

    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: Would validate $baseline_json" | tee -a "$validation_log"
        return 0
    fi

    if [ ! -f "$baseline_json" ]; then
        log "ERROR" "Cannot validate $tank_name - baseline.json not found"
        return 1
    fi

    # Run validation script
    python3 "$VALIDATOR_SCRIPT" "$baseline_json" > "$validation_log" 2>&1
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        vlog "Validation passed for $tank_name"
        return 0
    else
        log "ERROR" "Validation failed for $tank_name"
        cat "$validation_log" >> "$REPORT_FILE"
        return 1
    fi
}

# Process a single tank with retry logic
process_tank() {
    local tank_basename=$1
    local config_file="$CONFIG_DIR/${tank_basename}.yaml"

    # Verify config file exists
    if [ ! -f "$config_file" ]; then
        log "WARN" "Config file not found: $config_file"
        SKIPPED_TANKS+=("$tank_basename")
        return
    fi

    # Extract tank info from config
    local tank_name=$(get_tank_name "$config_file")
    local gender=$(get_tank_gender "$config_file")

    if [ -z "$tank_name" ]; then
        log "WARN" "Could not extract tank name from $config_file"
        SKIPPED_TANKS+=("$tank_basename")
        return
    fi

    echo -e "\n${BLUE}Processing Tank: $tank_name ($gender)${NC}"
    log "INFO" "Starting baseline for $tank_name (gender: $gender)"

    local attempt=1
    local success=false

    # Retry loop
    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "  Attempt $attempt/$MAX_RETRIES..."

        if run_baseline "$tank_name" "$gender" "$config_file" "$attempt"; then
            if validate_baseline "$tank_name" "$config_file"; then
                echo -e "  ${GREEN}✓ PASS${NC}"
                log "INFO" "Baseline successful for $tank_name (attempt $attempt)"
                PASS_TANKS+=("$tank_name")
                success=true
                break
            else
                echo -e "  ${YELLOW}⚠ Validation failed${NC}"
                log "WARN" "Baseline validation failed for $tank_name (attempt $attempt)"
            fi
        else
            echo -e "  ${YELLOW}⚠ Execution failed${NC}"
            log "WARN" "Baseline execution failed for $tank_name (attempt $attempt)"
        fi

        if [ $attempt -lt $MAX_RETRIES ]; then
            local wait_time=$((attempt * 5))
            echo "  Waiting ${wait_time}s before retry..."
            sleep "$wait_time"
        fi

        ((attempt++))
    done

    if [ "$success" = false ]; then
        echo -e "  ${RED}✗ FAIL${NC}"
        log "ERROR" "Baseline failed for $tank_name after $MAX_RETRIES attempts"
        FAIL_TANKS+=("$tank_name")
        if [ $attempt -gt 1 ]; then
            RETRY_TANKS+=("$tank_name")
        fi
    fi
}

# Main execution
main() {
    print_header | tee "$REPORT_FILE"

    # Check prerequisites
    if [ ! -f "$BASELINE_SCRIPT" ]; then
        log "ERROR" "Baseline script not found: $BASELINE_SCRIPT"
        exit 1
    fi

    if [ ! -f "$VALIDATOR_SCRIPT" ]; then
        log "ERROR" "Validator script not found: $VALIDATOR_SCRIPT"
        exit 1
    fi

    if [ ! -d "$CONFIG_DIR" ]; then
        log "ERROR" "Config directory not found: $CONFIG_DIR"
        exit 1
    fi

    # Get list of all tank configs
    local tanks=()
    while IFS= read -r config_file; do
        local basename=$(basename "$config_file" .yaml)
        tanks+=("$basename")
    done < <(find "$CONFIG_DIR" -maxdepth 1 -name "*.yaml" | sort)

    if [ ${#tanks[@]} -eq 0 ]; then
        log "ERROR" "No tank configurations found in $CONFIG_DIR"
        exit 1
    fi

    log "INFO" "Found ${#tanks[@]} tanks to process"
    vlog "Tanks: ${tanks[@]}"

    # Process each tank
    local tank_count=1
    local total_tanks=${#tanks[@]}
    for tank in "${tanks[@]}"; do
        echo ""
        echo -e "${BLUE}[${tank_count}/${total_tanks}]${NC}"
        process_tank "$tank"
        ((tank_count++))
    done

    # Print summary
    print_summary | tee -a "$REPORT_FILE"
}

# Print summary report
print_summary() {
    echo ""
    echo "======================================================================"
    echo "SUMMARY REPORT"
    echo "======================================================================"
    echo "End Time: $(date)"
    echo ""

    local pass_count=${#PASS_TANKS[@]}
    local fail_count=${#FAIL_TANKS[@]}
    local skip_count=${#SKIPPED_TANKS[@]}
    local total=$((pass_count + fail_count + skip_count))

    echo -e "${GREEN}PASSED: $pass_count${NC}"
    if [ $pass_count -gt 0 ]; then
        for tank in "${PASS_TANKS[@]}"; do
            echo "  ✓ $tank"
        done
    fi

    echo ""
    if [ ${#RETRY_TANKS[@]} -gt 0 ]; then
        echo -e "${YELLOW}RETRIED (but eventually passed): ${#RETRY_TANKS[@]}${NC}"
        for tank in "${RETRY_TANKS[@]}"; do
            echo "  ⟳ $tank"
        done
        echo ""
    fi

    echo -e "${RED}FAILED: $fail_count${NC}"
    if [ $fail_count -gt 0 ]; then
        for tank in "${FAIL_TANKS[@]}"; do
            echo "  ✗ $tank"
        done
    fi

    echo ""
    if [ $skip_count -gt 0 ]; then
        echo -e "${YELLOW}SKIPPED: $skip_count${NC}"
        for tank in "${SKIPPED_TANKS[@]}"; do
            echo "  ⊘ $tank"
        done
    fi

    echo ""
    echo "Total: $total | Passed: $pass_count | Failed: $fail_count | Skipped: $skip_count"
    echo ""
    echo "Report saved to: $REPORT_FILE"
    echo "Logs saved to: $LOG_DIR"
    echo "======================================================================"

    # Exit with appropriate code
    if [ $fail_count -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

# Run main
main
MAIN_EXIT=$?

exit $MAIN_EXIT
