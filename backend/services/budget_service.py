from typing import Dict, Any

class BudgetService:
    """
    A service class dedicated to calculating and distributing travel budgets.
    
    This service takes a total budget and splits it into standard percentage-based 
    allocations (Transport, Hotel, Food, Activities, and Emergency backup funds), 
    and also computes the individual share per traveler.
    """

    @staticmethod
    def calculate_allocation(total_budget: float, num_travelers: int) -> Dict[str, Any]:
        """
        Allocates the total travel budget into standard, pre-defined cost buckets and
        calculates the per-person distribution.
        
        Allocation Strategy:
        - Transport: 30% (Flights, train tickets, local transit, or cabs)
        - Hotel/Accommodation: 35% (Comfortable lodging tailored to the budget limit)
        - Food/Dining: 15% (Meals, street food experiences, and dining out)
        - Activities/Sightseeing: 10% (Entry tickets, tours, and experiences)
        - Emergency Backup: 10% (Unforeseen expenses, medical backup, or travel adjustments)
        
        Args:
            total_budget (float): The total budget available for the entire group.
            num_travelers (int): The total number of people traveling.
            
        Returns:
            Dict[str, Any]: A structured dictionary containing overall allocations and per-person allocations.
        """
        # Calculate categorical allocations based on standard proportions
        transport = total_budget * 0.30
        hotel = total_budget * 0.35
        food = total_budget * 0.15
        activities = total_budget * 0.10
        emergency = total_budget * 0.10

        # Build a complete, structured budget breakdown
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

