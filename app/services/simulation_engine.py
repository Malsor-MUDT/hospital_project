# simulation_engine.py
import numpy as np
import json
from datetime import datetime, timedelta
from app import db
from app.models.simulations import Simulation

class EnhancedSimulation:
    def __init__(self, hospital_id, devices, treatments):
        self.hospital_id = hospital_id
        self.devices = devices
        self.treatments = treatments
        
    def simulate_month_with_parameters(self, params):
        results = []
        
        for device in self.devices:
            device_id = device.device_id
            
            # Calculate actual treatments for this device
            avg_treatments = params['base_treatments_per_month'] * params['device_utilization_rates'].get(device_id, 0)
            
            # Apply seasonality
            avg_treatments *= params['seasonality_factor']
            
            # Apply maintenance downtime
            availability = 1 - params['maintenance_downtime'].get(device_id, 0)
            avg_treatments *= availability
            
            # Skip if no treatments expected
            if avg_treatments <= 0:
                continue
                
            revenues = []
            profits = []
            costs = []
            
            for _ in range(min(params['simulation_runs'], 100)):  # Limit to 100 runs for speed
                # Use negative binomial
                treatments_this_month = np.random.negative_binomial(
                    n=10,
                    p=10/(10 + avg_treatments)
                )
                
                # Calculate per treatment
                price = float(device.price_per_use) * params['price_changes'].get(device_id, 1.0)
                direct_cost = float(device.cost_per_use)
                staff_cost_per_min = (float(device.doctor_hourly_wage)/60 + float(device.nurse_hourly_wage)/60)
                staff_cost = staff_cost_per_min * (device.doctor_minutes + device.nurse_minutes)
                
                # Add fixed monthly costs
                fixed_monthly_cost = float(device.base_machine_cost) / 60
                
                revenue = treatments_this_month * price
                total_cost = treatments_this_month * (direct_cost + staff_cost) + fixed_monthly_cost
                profit = revenue - total_cost
                
                revenues.append(float(revenue))
                costs.append(float(total_cost))
                profits.append(float(profit))
            
            # Calculate breakeven (handle division by zero)
            variable_cost_per_use = direct_cost + staff_cost
            if price > variable_cost_per_use:
                breakeven = float(fixed_monthly_cost / (price - variable_cost_per_use))
            else:
                breakeven = None
            
            device_results = {
                'device_id': device_id,
                'device_name': device.device_type[:50],  # Limit name length
                'expected_treatments': float(avg_treatments),
                'expected_revenue': float(np.mean(revenues)) if revenues else 0.0,
                'expected_cost': float(np.mean(costs)) if costs else 0.0,
                'expected_profit': float(np.mean(profits)) if profits else 0.0,
                'probability_loss': float(np.mean([1 if p < 0 else 0 for p in profits])) if profits else 0.0,
                'breakeven_treatments': breakeven,
                'current_price': float(price),
                'variable_cost_per_use': float(variable_cost_per_use),
                'fixed_monthly_cost': float(fixed_monthly_cost),
                'gross_margin': float((price - variable_cost_per_use) / price) if price > 0 else 0.0
            }
            results.append(device_results)
        
        return results
    
    def optimize_prices(self, simulation_results, target_margin=0.20, elasticity=-0.3):
        recommendations = []
        
        if not simulation_results:
            return recommendations
        
        for result in simulation_results:
            device_name = result.get('device_name', 'Unknown')
            current_price = result.get('current_price', 0)
            variable_cost = result.get('variable_cost_per_use', 0)
            
            # Skip invalid data
            if current_price <= 0 or variable_cost <= 0:
                continue
            
            current_margin = (current_price - variable_cost) / current_price
            
            # Only recommend if margin is below target
            if current_margin < target_margin:
                required_price = variable_cost / (1 - target_margin)
                
                # Skip unreasonable recommendations
                if required_price <= 0 or required_price > current_price * 5:
                    continue
                
                price_change_pct = ((required_price / current_price) - 1) * 100
                demand_change_pct = elasticity * price_change_pct
                
                recommendations.append({
                    'device_name': device_name,
                    'current_price': current_price,
                    'recommended_price': required_price,
                    'current_margin': current_margin * 100,
                    'target_margin': target_margin * 100,
                    'price_change_pct': price_change_pct,
                    'demand_change_pct': demand_change_pct
                })
        
        return recommendations
    
    def save_simulation_simple(self, parameters, results, recommendations=None):
        """Simple save method that always works"""
        try:
            # Always rollback first
            db.session.rollback()
            
            # Create minimal summary
            summary = {
                "device_count": len(results),
                "total_revenue": 0.0,
                "total_profit": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if results:
                total_rev = sum(float(r.get('expected_revenue', 0) or 0) for r in results)
                total_prof = sum(float(r.get('expected_profit', 0) or 0) for r in results)
                summary["total_revenue"] = float(total_rev)
                summary["total_profit"] = float(total_prof)
            
            # Create device list (limited to 5 devices for size)
            device_list = []
            for i, r in enumerate(results[:5]):  # Only first 5 devices
                device_list.append({
                    'name': r.get('device_name', f'Device {i}'),
                    'profit': float(r.get('expected_profit', 0) or 0),
                    'margin': float(r.get('gross_margin', 0) or 0) * 100
                })
            summary['devices'] = device_list
            
            # Create simulation with VERY simple data
            simulation = Simulation(
                hospital_id=self.hospital_id,
                simulation_type="revenue_forecast",
                parameters=json.dumps({
                    "simulation_date": datetime.utcnow().isoformat(),
                    "base_treatments": parameters.get('base_treatments_per_month', 0),
                    "simulation_runs": parameters.get('simulation_runs', 0)
                }, default=str),
                results=json.dumps(summary, default=str),
                recommendations=json.dumps({"count": len(recommendations or [])}, default=str) if recommendations else None
            )
            
            db.session.add(simulation)
            db.session.commit()
            return simulation.simulation_id
            
        except Exception as e:
            db.session.rollback()
            print(f"Save error: {str(e)[:200]}")  # Print first 200 chars
            return None
    
    # Alternative even simpler method
    def save_simulation_minimal(self, parameters, results):
        """Minimal save - just store that simulation ran"""
        try:
            db.session.rollback()
            
            simulation = Simulation(
                hospital_id=self.hospital_id,
                simulation_type="revenue_forecast",
                parameters=json.dumps({"ran": True, "timestamp": datetime.utcnow().isoformat()}, default=str),
                results=json.dumps({"device_count": len(results)}, default=str),
                recommendations=None
            )
            
            db.session.add(simulation)
            db.session.commit()
            return simulation.simulation_id
            
        except Exception as e:
            db.session.rollback()
            print(f"Minimal save failed: {e}")
            return None