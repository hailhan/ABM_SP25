from mesa.batchrunner import batch_run
from model import CommunityModel
import pandas as pd

# Define parameters
params = {"width": 50, "height": 50,
          "seed": list(range(10)), 
          "authority_density":[0.0, 0.05, 0.1, 0.15, 0.2, 0.25],
          "reliability_min": [-1.0, -0.5, 0.0],
          "reliability_max": [0.0, 0.5, 1.0],
}

if __name__ == '__main__':
    results = batch_run(
        CommunityModel,
        parameters=params,
        max_steps=300, # seems that most of the models converge by this point
        number_processes=None,
        data_collection_period=1,
        display_progress=True,
    )

    df = pd.DataFrame(results)
    df.to_csv("batch_results.csv", index=False)