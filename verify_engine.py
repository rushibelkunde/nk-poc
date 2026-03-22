import analytics_engine
import json

def test_all():
    print("Testing Sales Prediction...")
    try:
        raw, meta = analytics_engine.run_sales_prediction()
        print("SUCCESS")
        # print(f"Raw: {raw[:100]}...")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Liquidity Risk...")
    try:
        raw, meta = analytics_engine.run_liquidity_risk()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Inventory Optimization...")
    try:
        raw, meta = analytics_engine.run_inventory_optimization()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Tax Delta...")
    try:
        raw, meta = analytics_engine.run_tax_delta()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Customer Health...")
    try:
        raw, meta = analytics_engine.run_customer_health()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Margin Velocity...")
    try:
        raw, meta = analytics_engine.run_margin_velocity()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Profitability Analysis...")
    try:
        raw, meta = analytics_engine.run_profitability_analysis()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\nTesting Working Capital Analysis...")
    try:
        raw, meta = analytics_engine.run_working_capital_analysis()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_all()
