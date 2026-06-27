from typing import Dict, Any

class BudgetService:
    @staticmethod
    def calculate_allocation(total_budget: float, num_travelers: int) -> Dict[str, Any]:
        """Allocates budget into standard buckets.
        
        Buckets:
        - Transport: 30%
        - Hotel: 35%
        - Food: 15%
        - Activities: 10%
        - Emergency: 10%
        """
        transport = total_budget * 0.30
        hotel = total_budget * 0.35
        food = total_budget * 0.15
        activities = total_budget * 0.10
        emergency = total_budget * 0.10

        return {
            "total_budget": total_budget,
            "num_travelers": num_travelers,
            "allocation": {
                "transport": round(transport, 2),
                "hotel": round(hotel, 2),
                "food": round(food, 2),
                "activities": round(activities, 2),
                "emergency": round(emergency, 2)
            },
            "per_person": {
                "total": round(total_budget / num_travelers, 2),
                "transport": round(transport / num_travelers, 2),
                "hotel": round(hotel / num_travelers, 2),
                "food": round(food / num_travelers, 2),
                "activities": round(activities / num_travelers, 2),
                "emergency": round(emergency / num_travelers, 2)
            }
        }
