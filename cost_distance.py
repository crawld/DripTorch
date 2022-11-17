import numpy as np
import heapq
import matplotlib.pyplot as plt
import pdb
# ref: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/understanding-cost-distance-analysis.htm  # noqa: E501
# ref: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/how-the-cost-distance-tools-work.htm  # noqa: E501
# ref: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

class Heap:
    def __init__(self,x = None):
        if x:
            self.list = x
        else:
            self.list = []
        heapq.heapify(self.list)

    def push(self,x):
        heapq.heappush(self.list,x)
    
    def pop(self):
        return heapq.heappop(self.list)



class Raster:
    def __init__(self,raster:np.ndarray,transform:np.ndarray=None,noData:float=np.nan) -> None:
        self.rows,self.cols = raster.shape
        self.raster = raster.flatten()
        self.inds = np.arange(self.raster.shape[0])
        self.neighbor_Kernel = [-self.cols-1,-self.cols,-self.cols+1,-1,1,self.cols-1,self.cols,self.cols+1] 
        if transform:
            self._world2ind = transform.copy()
            self._ind2world = np.linalg.inv(transform)

    def get_Index(self,index:int) -> np.ndarray:
        # Return the 2d index given the 1d index
        return np.array([index//self.cols,index%self.cols]).astype(int)
    
    def get_Neighbors(self,index:int) -> list:
        """
        Return the 1d neighborhood indicies for the neighborhood of a given pixel and check bounds
        -------+-------+-----
        -cols-1| -cols | -cols+1
        -------+-------+-----
        -1     | 0     | +1
        -------+-------+-----
        cols-1 | cols  | cols+1
        -------+-------+-----
        + index
        """
        
      
        matcoords = np.array(self.get_Index(index)) # get 2d coords
        neighborhood = self.neighbor_Kernel + index
        # check if we are at the boundary
        if matcoords[0] <= 0: # If we are at the first row
            neighborhood[:3] = -999
        if matcoords[0] >= self.rows-1: # If we are at the last row
            neighborhood[-3:] = -999
        if matcoords[1] <= self.cols-1: # If we are at the first column
            remove = [0,3,5]
            neighborhood[remove] = -999
        if matcoords[1] >= self.cols-1: # If we are at the last column
            remove = [2,4,7]
            neighborhood[remove] = -999
        
        # remove out of bounds inds
        neighborhood = list(filter(lambda x: x != -999, neighborhood))
    
        # get 2d locs of neighborhood
        locs = [self.get_Index(x) for x in neighborhood]
    
        # get 2d distance to each point and stash that with index in the tuple
        distances = [np.linalg.norm((x-matcoords)) for x in locs]
        
        # join neighborhood indicies and their respective distances from the origin point
        neighbors_dists = list(zip([index]*len(neighborhood),neighborhood,distances))
           
        return neighbors_dists

    def __getitem__(self,key):
        return self.raster[key]
    
    def __setitem__(self,key,item):
        self.raster[key] = item

    def world2ind(location,round=True) -> np.ndarray:
        # Map from spatial coordinates to raster coords
        if self._world2ind:
            point = [location[0],location[1],1]
            index = self._world2ind@point
            index = index[:-1]
            if round:
                index = index.astype(int)
            return index
        else:
            return None 

    def ind2world(index)-> np.ndarray:
        # Map from raster coordinates to world coords
        if self._ind2world:
            point = [index[0],index[1],1]
            world = self._ind2world@point
            return world[:-1]
        else:
            return None
    
class SourceRaster(Raster):
    def __init__(self,raster:np.ndarray):
        super().__init__(raster=raster)

    @property
    def locations(self) -> np.ndarray:
        return self.inds[self.raster]


class CostDistance:
    def __init__(self,source_raster,cost_raster,elevation_raster):
        self.source_raster = source_raster
        self.cost_raster = cost_raster
        self.elevation_raster = elev_raster
     
        source_neighbors = [self.source_raster.get_Neighbors(index) for index in  self.source_raster.locations]
        init_costs = self._compute_costs(source_neighbors)
        self.PQ = Heap(init_costs)
    
    def _compute_costs(self,edge_set:list) -> list:
        computed_costs = []
        for edges in edge_set:
            for edge in edges:
                start,stop,distance = edge
                dz = self.elevation_raster[start] - self.elevation_raster[stop]
                move_length = np.sqrt(distance**2 + dz**2)
                cost = self.cost_raster[start] + move_length
                computed_costs.append((cost,stop))
        return computed_costs
    
    def iterate(self) -> np.ndarray:
        while len(self.PQ.list) > 0:
            cost,loc = self.PQ.pop()
            if cost > self.cost_raster[loc]:
                continue
            else:
                self.cost_raster[loc] = cost
                neighbors = [self.cost_raster.get_Neighbors(loc)]
                neighbor_costs = self._compute_costs(neighbors)
                for c in neighbor_costs:
                    self.PQ.push(c)
        return self.cost_raster.raster.reshape((self.cost_raster.rows,self.cost_raster.cols))
       
        

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    elevs = np.load("/Users/franklyndunbar/Project/testarea.npy")
    source_raster = np.zeros_like(elevs).astype(bool)
    cost_raster = np.ones_like(elevs)
    cost_raster *= np.inf
    source_slice = np.s_[0,:]
    source_raster[source_slice] = True
    cost_raster[source_slice] = 0

    elev_raster = Raster(elevs)
    cost_raster = Raster(cost_raster)
    source_raster = SourceRaster(source_raster)

    CD = CostDistance(source_raster,cost_raster,elev_raster)
    test = CD.iterate()
    plt.rcParams["figure.figsize"] = (160/8,90/8)
    plt.imshow(test.reshape(cost_raster.rows,cost_raster.cols))
    plt.plot()
    plt.colorbar()
    plt.show()