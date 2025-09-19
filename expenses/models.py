from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    #Model to represent expense categories. Each category is owned by a specific user.
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        #ensure a user cannot have two categories with same name
        unique_together=("user","name")
        verbose_name_plural="categories"

    def __str__(self):
        return f"{self.name} (by {self.user.username})"
    
class Expense(models.Model):
    #model to represent an individual expense. each expense is linked to a user and a category.

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} - {self.category.name} on {self.date}"
    class Meta:
        #Orders expense by date, most recent first
        ordering = ['-date']