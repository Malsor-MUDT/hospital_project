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
            
            simulation_runs = min(params.get('simulation_runs', 100), 100)
            
            for _ in range(simulation_runs):
                # Use negative binomial
                treatments_this_month = np.random.negative_binomial(
                    n=10,
                    p=10/(10 + avg_treatments)
                )
                
                # Calculate per treatment
                price = float(device.price_per_use) * params['price_changes'].get(device_id, 1.0)
                direct_cost = float(device.cost_per_use)
                doctor_cost_per_min = float(device.doctor_hourly_wage) / 60
                nurse_cost_per_min = float(device.nurse_hourly_wage) / 60
                staff_cost = (doctor_cost_per_min * device.doctor_minutes) + (nurse_cost_per_min * device.nurse_minutes)
                
                # Add fixed monthly costs
                fixed_monthly_cost = float(device.base_machine_cost) / 60 if hasattr(device, 'base_machine_cost') else 0
                
                revenue = treatments_this_month * price
                total_cost = (treatments_this_month * (direct_cost + staff_cost)) + fixed_monthly_cost
                profit = revenue - total_cost
                
                revenues.append(float(revenue))
                costs.append(float(total_cost))
                profits.append(float(profit))
            
            # Calculate financial metrics
            expected_treatments = float(avg_treatments)
            expected_revenue = float(np.mean(revenues)) if revenues else 0.0
            expected_cost = float(np.mean(costs)) if costs else 0.0
            expected_profit = float(np.mean(profits)) if profits else 0.0
            
            # Calculate profit margin
            variable_cost_per_use = direct_cost + staff_cost
            gross_margin = (price - variable_cost_per_use) / price if price > 0 else 0
            
            # Probability of loss
            probability_loss = float(np.mean([1 if p < 0 else 0 for p in profits])) if profits else 0.0
            
            # Risk level
            if probability_loss >= 0.3:
                risk_level = 'high'
            elif probability_loss >= 0.1:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Breakeven
            if price > variable_cost_per_use:
                breakeven = float(fixed_monthly_cost / (price - variable_cost_per_use))
            else:
                breakeven = None
            
            device_results = {
                'device_id': device_id,
                'device_name': device.device_type,
                'expected_treatments': expected_treatments,
                'expected_revenue': expected_revenue,
                'expected_cost': expected_cost,
                'expected_profit': expected_profit,
                'current_price': float(price),
                'variable_cost_per_use': float(variable_cost_per_use),
                'fixed_monthly_cost': float(fixed_monthly_cost),
                'gross_margin': float(gross_margin),
                'probability_loss': probability_loss,
                'risk_level': risk_level,
                'breakeven_treatments': breakeven
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
        """Save simulation results with correct field names"""
        try:
            db.session.rollback()
            
            if not results or len(results) == 0:
                return None
            
            # Transform device data
            device_list = []
            for result in results:
                device_data = {
                    'device_name': result.get('device_name', 'Unknown Device'),
                    'expected_profit': float(result.get('expected_profit', 0)),
                    'gross_margin': float(result.get('gross_margin', 0)),
                    'expected_revenue': float(result.get('expected_revenue', 0)),
                    'expected_cost': float(result.get('expected_cost', 0)),
                    'expected_treatments': float(result.get('expected_treatments', 0)),
                    'current_price': float(result.get('current_price', 0)),
                    'variable_cost_per_use': float(result.get('variable_cost_per_use', 0)),
                    'fixed_monthly_cost': float(result.get('fixed_monthly_cost', 0)),
                    'probability_loss': float(result.get('probability_loss', 0)),
                    'risk_level': result.get('risk_level', 'medium'),
                    'breakeven_treatments': float(result.get('breakeven_treatments', 0)) if result.get('breakeven_treatments') else None
                }
                device_list.append(device_data)
            
            total_revenue = sum(d['expected_revenue'] for d in device_list)
            total_profit = sum(d['expected_profit'] for d in device_list)
            
            summary = {
                "device_count": len(device_list),
                "total_revenue": total_revenue,
                "total_profit": total_profit,
                "devices": device_list
            }
            
            simulation = Simulation(
                hospital_id=self.hospital_id,
                simulation_type="revenue_forecast",
                parameters=json.dumps(parameters, default=str),
                results=json.dumps(summary, default=str),
                recommendations=json.dumps(recommendations, default=str) if recommendations else None
            )
            
            db.session.add(simulation)
            db.session.commit()
            return simulation.simulation_id
            
        except Exception as e:
            db.session.rollback()
            print(f"Save error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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


# Optional: Create standalone functions if you prefer
def save_simulation_standalone(hospital_id, parameters, results, recommendations=None):
    """Alternative: Standalone save function"""
    try:
        db.session.rollback()
        
        if not results or len(results) == 0:
            return None
        
        device_list = []
        for result in results:
            device_data = {
                'device_name': result.get('device_name', 'Unknown Device'),
                'expected_profit': float(result.get('expected_profit', 0)),
                'gross_margin': float(result.get('gross_margin', 0)),
                'expected_revenue': float(result.get('expected_revenue', 0)),
                'expected_cost': float(result.get('expected_cost', 0)),
                'expected_treatments': float(result.get('expected_treatments', 0)),
                'current_price': float(result.get('current_price', 0)),
                'variable_cost_per_use': float(result.get('variable_cost_per_use', 0)),
                'fixed_monthly_cost': float(result.get('fixed_monthly_cost', 0)),
                'probability_loss': float(result.get('probability_loss', 0)),
                'risk_level': result.get('risk_level', 'medium'),
                'breakeven_treatments': float(result.get('breakeven_treatments', 0)) if result.get('breakeven_treatments') else None
            }
            device_list.append(device_data)
        
        total_revenue = sum(d['expected_revenue'] for d in device_list)
        total_profit = sum(d['expected_profit'] for d in device_list)
        
        summary = {
            "device_count": len(device_list),
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "devices": device_list
        }
        
        simulation = Simulation(
            hospital_id=hospital_id,
            simulation_type="revenue_forecast",
            parameters=json.dumps(parameters, default=str),
            results=json.dumps(summary, default=str),
            recommendations=json.dumps(recommendations, default=str) if recommendations else None
        )
        
        db.session.add(simulation)
        db.session.commit()
        return simulation.simulation_id
        
    except Exception as e:
        db.session.rollback()
        print(f"Standalone save error: {e}")
        return None