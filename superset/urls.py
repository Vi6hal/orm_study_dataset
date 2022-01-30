from datetime import datetime
from django.forms import ValidationError
from django.contrib.postgres.search import SearchVector
from django.urls import path, include
from django.http import HttpResponse
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.shortcuts import render
def test(request):
    from .models import Actor
    """
    Follow:
        https://github.com/Jkremr/pagila-queries

    Q1.Create a list of all the actors first name and last name. Display the first and last name of each actor in a single column in upper case letters. Name the column Actor Name.
    ANS:
        RAW SQL: SELECT first_name || ' ' || last_name AS "Actor Name" FROM actor;
        ORM QUERY:
        result = Actor.objects.annotate(
            actor_name=Concat('first_name', Value(' '), 'last_name',
            output_field=CharField())
            ).values("actor_name")
    
    Q2-A:Find the id, first name, and last name of an actor, of whom you know only the first name of "Joe."
    Q2-B:Find the id, first name, and last name of an actor, of whom you know only the first name of "Joe."
    
    ANS-A:
        RAW SQL:SELECT actor_id,first_name,last_name FROM actor WHERE first_name ILIKE 'joe';
        result = Actor.objects.raw('select actor_id,first_name,last_name FROM actor WHERE first_name ILIKE \'joe\'')
        
        contains is case-sensitive hence does not return any result
        result = Actor.objects.filter(first_name__contains='joe')

        search does not works (not supported by text field)
        result = Actor.objects.filter(first_name__search='joe')

        SearchVector works but performs a full text search
        result = Actor.objects.annotate(
            search=SearchVector('first_name')).filter(search='joe')

        icontain works: but it also translates to a like field lookup with a UPPER case coversion
        result = Actor.objects.filter(first_name__icontains='joe')
    ANS-B:
        RAW SQL:SELECT actor_id,first_name ,last_name FROM actor WHERE last_name ILIKE '%gen%';
        result = Actor.objects.filter(last_name__icontains='gen')


    Q3: Using IN, display the country_id and country columns of the following countries: Afghanistan, Bangladesh, and China
    ANS:
        RAW SQL: select * from country where country
    from .models import Country
    # result = Country.objects.filter(country__in=('Afghanistan', 'Bangladesh','China'))
    result = Country.objects.raw("SELECT * FROM country WHERE country IN ('Afghanistan','Bangladesh','China')")

    Q4-A: List the last names of actors, as well as how many actors have that last name.
    Q4-B: List last names of actors and the number of actors who have that last name, but only for names that are shared by at least two actors.
    
    ANS:
        4-A-RAW SQL: select last_name,count(last_name) as ln_count from actor group by last_name order by ln_count desc
        from django.db.models import Count
        result = Actor.objects.values('last_name',).annotate(ln_count=Count('last_name')).order_by('-ln_count')

        4-B-RAW SQL: select last_name,count(last_name) as ln_count from actor group by last_name HAVING ln_count >= 2 order by ln_count desc
        result = Actor.objects.values('last_name',).annotate(ln_count=Count('last_name')).filter(ln_count_gte=2).order_by('-ln_count')
           
        Q5: Use a JOIN to display the first and last names, as well as the address, of each staff member. (Use the tables staff and address)
        ANS:
            RAW-SQL:SELECT staff.first_name , staff.last_name , address.address AS address FROM staff INNER JOIN address ON address.address_id = staff.address_id;
            Building the ORM Query: 
                Staff.objects.all().values("first_name","last_name","address")
                in the above query only the id's of the addresses are fetched but we can use 
            JOIN QUERY EXAMPLES
            Outer Join:
            - SELECT staff.first_name , staff.last_name , address.address AS address FROM staff RIGHT OUTER JOIN address ON address.address_id = staff.address_id;
            - SELECT staff.first_name , staff.last_name , address.address AS address FROM staff LEFT OUTER JOIN address ON address.address_id = staff.address_id;
            
            ORM:
            You cannot directly perform a join on the table using a model query, the orm decides wether to make a left outer join or a right outer join.
            to convert this query into a right outer join 
            result = Address.objects.all().values("address","staff__first_name","staff__last_name")

            Inner Join(default join):
            SELECT staff.first_name , staff.last_name , address.address AS address FROM staff JOIN address ON address.address_id = staff.address_id;
            SELECT staff.first_name , staff.last_name , address.address AS address FROM staff INNER JOIN address ON address.address_id = staff.address_id;
        
        Q6:Use a JOIN to display the total amount rung up by each staff member in January of 2007. Use tables staff and payment.
        ANS:
            RAW SQL:
                Option 1:
                select staff.first_name,staff.last_name, sum("amount") as amt,count(customer_id) as orders
                    from payment 
                    join staff on staff.staff_id=payment.staff_id
                    where payment.payment_date::date between '01/01/2007' and '01/02/2021'
                    group by payment.staff_id,staff.first_name
                    order by amt
                Option 2:
                select aas.first_name,bas.staff_id,bas.sum_amt from 
                    (select staff_id,first_name from staff) as aas,
                    (select staff_id,sum(amount) as sum_amt from payment group by staff_id) as bas
                where aas.staff_id=bas.staff_id

            django's ORM does not support join without f.k hence it will be a two step query
            from .models import Staff,Address,Customer,Payment
            from django.db.models import Sum 
            result = Payment.objects.filter(payment_date__range=[datetime(2007,1,1).date(),datetime(2007,2,1).date()]).values_list("staff_id").annotate(sales=Sum("amount")).order_by("-sales")
            result = Staff.objects.all().values("first_name","last_name")
        
        Q7:List each film and the number of actors who are listed for that film.
        ANS:
            RAW SQL:
                SELECT film.title,film.film_id,COUNT(film_actor.actor_id) AS actor_count
                FROM film
                INNER JOIN film_actor ON film.film_id = film_actor.film_id
                GROUP BY film.title,film.film_id
                ORDER BY COUNT(film_actor.actor_id),film.title
            ORM:
                from .models import Film,FilmActor
                from django.db.models import Count
                result = FilmActor.objects.values("film","film__title").annotate(actors=Count("actor")).order_by("actors","film__title")

        Q8: How many copies of the film Hunchback Impossible exist in the inventory system?
        ANS:
            RAW SQL:
                select film_id,count(inventory_id) from inventory
                where film_id=(
                    select film_id from film 
                    where title ilike 'hunchback impossible' limit 1)
                group by film_id
            ORM 
                from .models import Film,Inventory
                from django.db.models import Count
                result = Inventory.objects.filter(film__title__icontains="HUNCHBACK IMPOSSIBLE").values("film","film__title").annotate(count=Count("film"))
                result = Film.objects.filter(title__icontains="HUNCHBACK IMPOSSIBLE").values("film_id","title").annotate(count=Count("inventory"))


        Q9:display all actors who appear in the film Alone Trip.
        Note: Try to use subqueries
        ANS:
            RAW SQL:

            result = Film.objects.filter(title__icontains="alone trip").values("filmactor","filmactor__actor__first_name","filmactor__actor__last_name")


"""
    from .models import Film,FilmActor
    from django.db.models import Count
    result = Film.objects.filter(title__icontains="alone trip").values("film_id","filmactor","filmactor__actor__first_name","filmactor__actor__last_name")







    for item in result:
        print(item)
    # print(result)
    return render("superset/hello.html",)

urlpatterns = [
 path("",test)
]