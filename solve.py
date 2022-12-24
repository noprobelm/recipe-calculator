import networkx as nx
import pandas as pd
from pandas._typing import FilePath, ReadCsvBuffer, ReadCsvBuffer
from typing import Union, Optional
from rich.prompt import Prompt
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def build_graph(path_to_csv: Union[FilePath, ReadCsvBuffer[bytes], ReadCsvBuffer[str]]) -> nx.DiGraph:
    """Build a directed graph using a csv-formatted edge list

    Returns:
        satisfactory_recipe_digraph (nx.DiGraph): DiGraph structure containing all recipes, ingredients, and their
        relationships as a directed graph.
    """
    satisfactory_edge_list = pd.read_csv(path_to_csv)
    satisfactory_recipe_digraph = nx.from_pandas_edgelist(
        satisfactory_edge_list, source="Recipe", target="Ingredient", edge_attr=True, create_using=nx.DiGraph
    )
    return satisfactory_recipe_digraph


def get_ingredients(
    graph: nx.DiGraph, recipe: str, num_output: Optional[Union[int, float]] = 1
) -> dict[str, dict[str, int]]:
    """
    This algorithm works by taking a networkx digraph containing relationships between recipes and their ingredients and
    outputting the number of ingredients required to produce X of a recipe.

    The algorithm is fairly simple, but more complex than simply discovering each predecessor vertex from our target
    recipe. Since we're interested in quantities, and a given recipe's predecessors can then have identical predecessors
    somewhere further along, we must iteratively account for the base recipe's predecessors, then each predecessor for
    each additional ingredient along the path. After the simple edge path of all predecessor ingredients have been
    accounted for, we will have accessed all the information we need. A short summary of the way this algorithm works:

    1. Take a directed graph containing a set of recipes. The edges between each vertex must host whatever information
    we need for our calculation. In this case, we only need to know about the number of ingredients (labeled "Ingredient
    Rate")required to produce 'num_output' of a recipe.
    2. Create a subgraph composed of only a specific recipe among the given graph and its predecessor vertices
    3. Create a dictionary 'ingredients' for each ingredient among our subgraph whose starting value are 0 (with the
    exception of the recipe itself, whose value is 'num_output').
    4. Iterate through each ingredient in the dictionary and store all possible paths between the subject ingredient
    and the target recipe using a simple edge path algorithm.
    5. Iterate through each path we discovered for a single ingredient to the target recipe
        - We know we need 'num_output' of recipe, so set variable 'product' to this at the start of each path.
        - Traverse the path between 'recipe' and 'ingredient', setting 'product' to the product of itself and the number
        of required ingredients to produce X of its successor
        - After all simple edge paths for a single path have been traversed, increment the ingredients dictionary by
        the number of ingredients we calculated
    6. Repeat steps 4 and 5 until all ingredients have been explored

    The end result is a dictionary of all ingredients and their quantities required to produce 'num_output' of a target
    recipe.

    Args:
        - recipe (str): The name of the recipe we'd like to produce
        - num_output (int): number of the recipe to be output. Default: 1

    Parameters:
        - graph (nx.DiGraph): The graph generated from our edge list
        - p (dict): All targets from source whose values are the sources they are linked to.
        - sg: (nx.DiGraph): A subgraph from 'graph'
        - ingredients (dict): All ingredients whose values are the number required to produce 'num_output' of source
    Returns:
        - ingredients (dict): All ingredients whose values are the number required to produce 'num_output' of source
    """

    p = nx.predecessor(graph, recipe)
    sg = nx.subgraph(graph, p)
    ingredients = dict(zip([n for n in sg.nodes], [0 for n in range(len(sg.nodes))]))
    ingredients[recipe] = num_output
    for ing in ingredients:
        paths = [path for path in nx.all_simple_edge_paths(sg, recipe, ing)]
        for path in paths:
            product = num_output
            for u, v in path:
                product *= sg.edges[u, v]["Ingredient Rate"]
            ingredients[ing] += product

    del ingredients[recipe]
    return ingredients


if __name__ == '__main__':
    console = Console()
    graph = build_graph('data/satisfactory_edge_list.csv')

    nodes = Panel(Columns([node for node in graph.nodes], equal=True, expand=True))
    console.print(nodes, style='indian_red')
    # TODO: Add error handling for invalid recipe inputs
    recipe = Prompt.ask("Enter one of a valid recipe from list above").title()
    num_output = Prompt.ask("Input number of desired recipe to output (default=1)")
    try:
        num_output = float(num_output)
    except ValueError:
        num_output = 1
    args = [graph, recipe, num_output]
    ingredients = get_ingredients(*args)

    table = Table(title=Text(f"{num_output} of {recipe}", 'indian_red'), style='indian_red', show_header=False,
                  show_lines=True)
    for ingredient in ingredients:
        table.add_row(ingredient, str(ingredients[ingredient]))
    console.print(table)
