"""
AI Supply Chain Intelligence System - Main Orchestrator

Usage:
    python run.py              # Full pipeline (web scraping + all agents)
    python run.py --quick      # Skip web scraping, use seed data only
    python run.py --report-only  # Regenerate report from last analysis results
"""

import json
import os
import sys
import argparse
import datetime
import traceback

# Add project root to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config

def _import_agent(name):
    """agents/ 디렉토리에서 에이전트 모듈을 동적으로 임포트."""
    import importlib.util, os
    path = os.path.join(BASE_DIR, "agents", f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

data_agent       = _import_agent("data_agent")
mapping_agent    = _import_agent("mapping_agent")
modeling_agent   = _import_agent("modeling_agent")
bottleneck_agent = _import_agent("bottleneck_agent")
strategy_agent   = _import_agent("strategy_agent")
report_agent     = _import_agent("report_agent")

# Supply-Demand Intelligence Engine (공시 기반 수급갭 분석)
try:
    earnings_agent = _import_agent("earnings_agent")
    demand_mapper  = _import_agent("demand_mapper")
    gap_engine     = _import_agent("gap_engine")
    SUPPLY_INTEL_AVAILABLE = True
except Exception as _e:
    earnings_agent = demand_mapper = gap_engine = None
    SUPPLY_INTEL_AVAILABLE = False
    print(f"[WARNING] Supply-Demand Intelligence Engine 로드 실패: {_e}")

try:
    db_agent = _import_agent("db_agent")
    DB_AGENT_AVAILABLE = True
except Exception:
    db_agent = None
    DB_AGENT_AVAILABLE = False

try:
    word_agent = _import_agent("word_agent")
    WORD_AGENT_AVAILABLE = True
except Exception:
    word_agent = None
    WORD_AGENT_AVAILABLE = False

try:
    dynamics_agent = _import_agent("dynamics_agent")
    DYNAMICS_AGENT_AVAILABLE = True
except Exception as _e:
    dynamics_agent = None
    DYNAMICS_AGENT_AVAILABLE = False
    print(f"[WARNING] Dynamics Agent 로드 실패: {_e}")


def load_run_state():
    """Load previous run state if available."""
    if os.path.exists(config.RUN_STATE_PATH):
        try:
            with open(config.RUN_STATE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_run_state(state):
    """Save current run state."""
    os.makedirs(os.path.dirname(config.RUN_STATE_PATH), exist_ok=True)
    with open(config.RUN_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def load_market_state():
    """Load market state from previous data agent run."""
    if os.path.exists(config.MARKET_STATE_PATH):
        try:
            with open(config.MARKET_STATE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def print_banner():
    """Print system banner."""
    print()
    print("=" * 70)
    print("  AI Supply Chain Intelligence System v1.0")
    print("  Token Demand -> Hardware Demand | Bottleneck Detection | Investment Signals")
    print(f"  Date: {datetime.date.today()}")
    print("=" * 70)
    print()


def print_step(step_num, total, name):
    """Print step progress."""
    print(f"\n[{step_num}/{total}] {name}")
    print("-" * 50)


def run_full_pipeline(quick=False, report_only=False, db_only=False, skip_supply=False):
    """Execute the full agent pipeline."""
    print_banner()

    run_state = load_run_state()
    run_state["last_run_start"] = str(datetime.datetime.now())
    base_mode = "quick" if quick else ("report_only" if report_only else ("db_only" if db_only else "full"))
    run_state["mode"] = base_mode + ("+skip_supply" if skip_supply else "")

    results = {}
    start_time = datetime.datetime.now()

    # ============================================================
    # DB-ONLY MODE: 마지막 결과를 DB에 저장하고 종료
    # ============================================================
    if db_only:
        print("\n[DB-Only Mode] 마지막 분석 결과를 DB에 저장합니다.")
        mapping_results  = None
        modeling_results = None
        bottleneck_results = None
        strategy_results = None
        db_results = {"db_available": False, "db_url": "unavailable"}
        if DB_AGENT_AVAILABLE:
            print_step(1, 1, "DB Agent")
            try:
                db_agent.init_db()
                db_results = db_agent.save_all(
                    mapping_result=mapping_results,
                    modeling_result=modeling_results,
                    bottleneck_result=bottleneck_results,
                    strategy_result=strategy_results,
                )
                results["db"] = "success" if db_results else "fallback"
            except Exception as e:
                print(f"  [ERROR] DB agent failed: {e}")
                results["db"] = "failed"
        else:
            print("  [SKIP] db_agent 로드 실패")
            results["db"] = "skip"
        end_time = datetime.datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print(f"\n  DB 상태: {'연결 성공' if db_results.get('db_available') else 'fallback (psycopg2 미설치 또는 연결 불가)'}")
        print(f"  Total runtime: {elapsed:.1f}s\n")
        return {"results": results, "elapsed": elapsed}

    # ============================================================
    # STEP 1: Data Agent
    # ============================================================
    total_steps = 12
    print_step(1, total_steps, "Data Intelligence Agent")
    if report_only:
        print("  [SKIP] Report-only mode: loading existing market state")
        data_results = load_market_state()
        if not data_results:
            print("  [WARNING] No market state found, running data agent")
            data_results = data_agent.run(quick=True)
    else:
        try:
            data_results = data_agent.run(quick=quick)
            results["data"] = "success"
            print(f"  [OK] Data agent completed")
        except Exception as e:
            print(f"  [ERROR] Data agent failed: {e}")
            traceback.print_exc()
            data_results = load_market_state()
            if data_results:
                print("  [FALLBACK] Using cached market state")
                results["data"] = "fallback"
            else:
                print("  [WARNING] No fallback available, using None")
                data_results = None
                results["data"] = "failed"

    # ============================================================
    # STEP 2: Mapping Agent
    # ============================================================
    print_step(2, total_steps, "Supply Chain Mapping Agent")
    try:
        mapping_results = mapping_agent.run(market_state=data_results)
        results["mapping"] = "success"
        print(f"  [OK] Mapping agent completed")
    except Exception as e:
        print(f"  [ERROR] Mapping agent failed: {e}")
        traceback.print_exc()
        mapping_results = None
        results["mapping"] = "failed"

    # ============================================================
    # STEP 3: Modeling Agent
    # ============================================================
    print_step(3, total_steps, "Quantitative Modeling Agent")
    try:
        modeling_results = modeling_agent.run(market_state=data_results)
        results["modeling"] = "success"
        print(f"  [OK] Modeling agent completed")
    except Exception as e:
        print(f"  [ERROR] Modeling agent failed: {e}")
        traceback.print_exc()
        modeling_results = None
        results["modeling"] = "failed"

    # ============================================================
    # STEP 4: Earnings Agent (공급 수치 수집 — 공시 기반)
    # ============================================================
    supply_state = demand_state = gap_report = None
    print_step(4, total_steps, "Earnings Agent (공급 수치 수집)")
    if SUPPLY_INTEL_AVAILABLE and not skip_supply and not report_only:
        try:
            supply_state = earnings_agent.run()
            results["earnings"] = "success"
            print(f"  [OK] Earnings agent completed")
        except Exception as e:
            print(f"  [ERROR] Earnings agent failed: {e}")
            traceback.print_exc()
            supply_state = earnings_agent.load_supply_state()
            results["earnings"] = "fallback" if supply_state else "failed"
            if supply_state:
                print("  [FALLBACK] Using cached supply_state.json")
    elif report_only:
        supply_state = earnings_agent.load_supply_state() if SUPPLY_INTEL_AVAILABLE else None
        results["earnings"] = "skip (report-only)"
        print("  [SKIP] report-only mode — loading cached supply_state")
    else:
        results["earnings"] = "skip"
        print("  [SKIP] supply intelligence disabled (--skip-supply)")

    # ============================================================
    # STEP 5: Demand Mapper (고객 수요 역산)
    # ============================================================
    print_step(5, total_steps, "Demand Mapper (고객 수요 역산)")
    if SUPPLY_INTEL_AVAILABLE and not skip_supply and not report_only:
        try:
            demand_state = demand_mapper.run()
            results["demand"] = "success"
            print(f"  [OK] Demand mapper completed")
        except Exception as e:
            print(f"  [ERROR] Demand mapper failed: {e}")
            traceback.print_exc()
            demand_state = demand_mapper.load_demand_state()
            results["demand"] = "fallback" if demand_state else "failed"
            if demand_state:
                print("  [FALLBACK] Using cached demand_state.json")
    elif report_only:
        demand_state = demand_mapper.load_demand_state() if SUPPLY_INTEL_AVAILABLE else None
        results["demand"] = "skip (report-only)"
        print("  [SKIP] report-only mode — loading cached demand_state")
    else:
        results["demand"] = "skip"
        print("  [SKIP] supply intelligence disabled (--skip-supply)")

    # ============================================================
    # STEP 6: Gap Engine (수급 갭 분석)
    # ============================================================
    print_step(6, total_steps, "Gap Engine (수급 갭 분석)")
    if SUPPLY_INTEL_AVAILABLE and not skip_supply and not report_only:
        try:
            gap_report = gap_engine.run(
                supply_state=supply_state,
                demand_state=demand_state,
            )
            results["gap"] = "success"
            print(f"  [OK] Gap engine completed")
        except Exception as e:
            print(f"  [ERROR] Gap engine failed: {e}")
            traceback.print_exc()
            gap_report = gap_engine.load_gap_report()
            results["gap"] = "fallback" if gap_report else "failed"
            if gap_report:
                print("  [FALLBACK] Using cached gap_report.json")
    elif report_only:
        gap_report = gap_engine.load_gap_report() if SUPPLY_INTEL_AVAILABLE else None
        results["gap"] = "skip (report-only)"
        print("  [SKIP] report-only mode — loading cached gap_report")
    else:
        results["gap"] = "skip"
        print("  [SKIP] supply intelligence disabled (--skip-supply)")

    # ============================================================
    # STEP 7: Supply-Demand Dynamics Agent
    # ============================================================
    print_step(7, total_steps, "Supply-Demand Dynamics Agent")
    dynamics_results = None
    if DYNAMICS_AGENT_AVAILABLE:
        try:
            dynamics_results = dynamics_agent.run(modeling_results=modeling_results)
            results["dynamics"] = "success"
            print(f"  [OK] Dynamics agent completed")
        except Exception as e:
            print(f"  [ERROR] Dynamics agent failed: {e}")
            traceback.print_exc()
            dynamics_results = dynamics_agent.load_dynamics_state()
            results["dynamics"] = "fallback" if dynamics_results else "failed"
    else:
        print("  [--] dynamics_agent 로드 실패 — 건너뜀")
        results["dynamics"] = "skip"

    # ============================================================
    # STEP 8: Bottleneck Agent  (gap_report.json 자동 연동)
    # ============================================================
    print_step(8, total_steps, "Bottleneck Detection Agent")
    try:
        bottleneck_results = bottleneck_agent.run(
            market_state=data_results,
            modeling_results=modeling_results
        )
        results["bottleneck"] = "success"
        print(f"  [OK] Bottleneck agent completed")
    except Exception as e:
        print(f"  [ERROR] Bottleneck agent failed: {e}")
        traceback.print_exc()
        bottleneck_results = None
        results["bottleneck"] = "failed"

    # ============================================================
    # STEP 9: Strategy Agent
    # ============================================================
    print_step(9, total_steps, "Strategy & Investment Agent")
    try:
        strategy_results = strategy_agent.run(
            bottleneck_results=bottleneck_results,
            modeling_results=modeling_results,
            mapping_results=mapping_results,
            market_state=data_results
        )
        results["strategy"] = "success"
        print(f"  [OK] Strategy agent completed")
    except Exception as e:
        print(f"  [ERROR] Strategy agent failed: {e}")
        traceback.print_exc()
        strategy_results = None
        results["strategy"] = "failed"

    # ============================================================
    # STEP 10: DB Agent
    # ============================================================
    print_step(10, total_steps, "DB Agent (PostgreSQL)")
    db_results = {"db_available": False, "db_url": "unavailable"}
    if DB_AGENT_AVAILABLE:
        try:
            db_ok = db_agent.init_db()
            saved = False
            if db_ok:
                saved = db_agent.save_all(
                    mapping_result=mapping_results,
                    modeling_result=modeling_results,
                    bottleneck_result=bottleneck_results,
                    strategy_result=strategy_results,
                )
            db_results = {"db_available": db_ok, "db_url": db_agent.DB_URL if db_ok else "unavailable"}
            results["db"] = "success" if saved else "fallback"
            print(f"  [OK] DB agent completed (db_available={db_ok}, saved={saved})")
        except Exception as e:
            print(f"  [~~] DB agent: {e} — fallback")
            results["db"] = "fallback"
    else:
        print("  [--] db_agent 로드 실패 — 건너뜀")
        results["db"] = "skip"

    # ============================================================
    # STEP 11: Report Agent
    # ============================================================
    print_step(11, total_steps, "Report & Visualization Agent")
    try:
        report_results = report_agent.run(
            data_results=data_results,
            mapping_results=mapping_results,
            modeling_results=modeling_results,
            bottleneck_results=bottleneck_results,
            strategy_results=strategy_results
        )
        results["report"] = "success"
        print(f"  [OK] Report agent completed")
    except Exception as e:
        print(f"  [ERROR] Report agent failed: {e}")
        traceback.print_exc()
        report_results = {"html_path": None, "pptx_path": None}
        results["report"] = "failed"

    # ============================================================
    # STEP 12: Word Agent
    # ============================================================
    print_step(12, total_steps, "Word Report Agent (한국어 학습 문서)")
    word_results = {"word_path": None}
    if WORD_AGENT_AVAILABLE:
        try:
            word_results = word_agent.run(
                state=data_results,
                bottleneck=bottleneck_results,
                strategy=strategy_results,
                modeling=modeling_results,
                mapping=mapping_results,
            )
            results["word"] = "success"
            print(f"  [OK] Word agent completed")
        except Exception as e:
            print(f"  [ERROR] Word agent failed: {e}")
            traceback.print_exc()
            results["word"] = "failed"
    else:
        print("  [--] word_agent 로드 실패 — 건너뜀")
        results["word"] = "skip"

    # ============================================================
    # SUMMARY
    # ============================================================
    end_time = datetime.datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)

    # Agent status summary
    print("\nAgent Status:")
    status_icons = {"success": "[OK]", "fallback": "[~~]", "failed": "[!!]", "skip": "[--]"}
    for agent_name, status in results.items():
        icon = status_icons.get(status, "[??]")
        print(f"  {icon} {agent_name.capitalize()}: {status}")

    print(f"\nTotal runtime: {elapsed:.1f}s")

    # Output files
    print("\nOutput Files:")
    if report_results.get("html_path"):
        print(f"  HTML Dashboard: {report_results['html_path']}")
        print(f"  HTML Latest:    {report_results.get('html_latest', 'N/A')}")
    if report_results.get("pptx_path"):
        print(f"  PowerPoint:     {report_results['pptx_path']}")
    else:
        print("  PowerPoint:     Not generated (check python-pptx installation)")
    _word_path = word_results.get("word_path") if word_results else None
    if _word_path:
        print(f"  Word Document:  {_word_path}")
    else:
        print("  Word Document:  Not generated (python-docx 미설치 또는 오류)")
    _db_ok = db_results.get("db_available", False)
    print(f"  DB Status:      {'연결 성공 (' + db_results.get('db_url','') + ')' if _db_ok else 'fallback (psycopg2 미설치 또는 연결 불가)'}")

    # Key findings
    print("\nKey Findings:")
    if gap_report and gap_report.get("layers"):
        layers = gap_report["layers"]
        print("  Supply-Demand Gap:")
        for layer_name, layer_data in layers.items():
            ratio = layer_data.get("gap_ratio")
            status = layer_data.get("gap_status", "?")
            conf = layer_data.get("supply_confidence", "?")
            ratio_str = f"{ratio:.2f}x" if isinstance(ratio, (int, float)) else "?"
            print(f"    {layer_name:10s}: {ratio_str} ({status}) conf={conf}")
    if bottleneck_results:
        primary = bottleneck_results.get("current_bottleneck", "N/A")
        util = bottleneck_results.get("current_utilization", 0)
        next_b = bottleneck_results.get("next_bottleneck", "N/A")
        print(f"  Primary Bottleneck: {primary} ({util:.0%} utilization)")
        print(f"  Next Bottleneck:    {next_b}")

    if modeling_results:
        snap = modeling_results.get("current_snapshot", modeling_results.get("current_snapshot_2025", {}))
        curr_yr = modeling_results.get("current_year", 2026)
        print(f"  {curr_yr} Token Demand:  {snap.get('total_tokens_per_day_fmt', 'N/A')}/day  ← 현재")
        print(f"  {curr_yr} GPU Required:  {snap.get('gpu_count_fmt', 'N/A')} (H100-equiv)  ← 현재")
        print(f"  {curr_yr} HBM Demand:    {snap.get('hbm_demand_fmt', 'N/A')}  ← 현재")

    if dynamics_results:
        dyn_base = dynamics_results.get("scenarios", {}).get("base", {}).get("2026", {})
        dyn_deploy = dyn_base.get("deployment", {})
        if dyn_deploy:
            print(f"  Dynamics Limit:      {dyn_deploy.get('limiting_layer', 'N/A')}")
            print(f"  Fulfillment Rate:    {dyn_deploy.get('fulfillment_rate', 0):.0%}")

    if strategy_results:
        phase = strategy_results.get("phase_position", "N/A")
        strong_buys = strategy_results.get("strong_buy_companies", [])
        print(f"  Investment Phase:   {phase}")
        print(f"  Strong Buy:         {', '.join(strong_buys)}")

    print()

    # Save run state
    run_state["last_run_end"] = str(datetime.datetime.now())
    run_state["last_run_elapsed_sec"] = elapsed
    run_state["last_agent_status"] = results
    run_state["last_outputs"] = {
        "html":  report_results.get("html_path"),
        "pptx":  report_results.get("pptx_path"),
        "word":  word_results.get("word_path") if word_results else None,
        "db_ok": db_results.get("db_available", False),
        "dynamics": getattr(dynamics_agent, "DYNAMICS_STATE_PATH", None) if dynamics_results else None,
    }
    save_run_state(run_state)

    return {
        "results": results,
        "report":  report_results,
        "word":    word_results,
        "db":      db_results,
        "dynamics": dynamics_results,
        "elapsed": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="AI Supply Chain Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py               Full pipeline with web scraping
  python run.py --quick       Fast mode using seed data only (no web)
  python run.py --report-only Regenerate reports from last analysis
        """
    )
    parser.add_argument("--quick", action="store_true",
                        help="Skip web scraping, use seed data only")
    parser.add_argument("--report-only", action="store_true",
                        help="Regenerate reports from last analysis results")
    parser.add_argument("--db-only", action="store_true",
                        help="DB 저장만 실행 (마지막 분석 결과 기반)")
    parser.add_argument("--skip-supply", action="store_true",
                        help="Supply-Demand Intelligence Engine 건너뜀 (earnings/demand/gap)")

    args = parser.parse_args()

    run_full_pipeline(
        quick=args.quick,
        report_only=args.report_only,
        db_only=args.db_only,
        skip_supply=args.skip_supply,
    )


if __name__ == "__main__":
    main()
