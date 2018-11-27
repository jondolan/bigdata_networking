# Libraries
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.stats import kde
from PIL import Image

# takes in python arrays of x and y data, outputs image to file
def generate(output, x, y):

    # create np arrays with the input arrays
    x = np.array(x)
    y = np.array(y)

    print("Creating plot...")
    fig = plt.figure()
    fig.set_size_inches((72, 36))   # set the size for output to be of sufficient resolution for cesium
    # set the plot limits and turn off autoscaling
    plt.xlim(-180.0, 180.0)
    plt.ylim(-90.0, 90.0)
    plt.autoscale(False)
    plt.axis('off') # hide the axis

    print("Creating gaussian distribution...")
    nbins = 50
    k = kde.gaussian_kde(np.stack((x,y)))
    print("Creating grid...")
    xi, yi = np.mgrid[-180:180:nbins*1j, -90:90:nbins*1j]
    print("Evaluating Gaussian over grid points...")
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))

    print("Plotting...")
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape), shading='gouraud', cmap='hot') # heatmap
    plt.scatter(x,y, c='w', s=1) # scatter plot

    print("Saving image...")
    plt.savefig(output, bbox_inches='tight', dpi=100)
    # clean up the image with Pillow
    img = Image.open(output)
    # crop out the axes...why matplotlib why
    area = (49, 9, 5629, 2781)
    img = img.crop(area)
    img = img.resize((4000, 1987), Image.ANTIALIAS)
    #img.putalpha(128) # no longer needed, applied in cesium
    img.save(output)

    print("Done outputting heatmap")
