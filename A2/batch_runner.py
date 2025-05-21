from mesa.batchrunner import batch_run
from model import CommunityModel
import pandas as pd

# Define parameters
params = {"width": 50, "height": 50,
          "seed": list(range(10)), "authority":[True,False], 
          "authority_density":[0.25, 0.5, 0.75]
}

if __name__ == '__main__':
    results = batch_run(
        CommunityModel,
        parameters=params,
        iterations=5,
        max_steps=100,
        number_processes=None,
        data_collection_period=1,
        display_progress=True,
    )

    df = pd.DataFrame(results)
    df.to_csv("batch_results.csv", index=False)