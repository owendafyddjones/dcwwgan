from sklearn import datasets
from tengan import dataGAN
from wgan import wGAN
from data.dataman import dagpolt,show_loss_progress
from math import ceil
import numpy as np
from fid import calculate_fid
from data.prepocessing import import_penguin,unnormalize

def marathon_mode(mygan,database,batch,noise_dim,filepath,epochs):
    """
    In marathon mode the GAN is trained for 50000 epochs and subtracted from the number of epochs left.
    Then the GAN model and the loss tracking is saved,
    the current loss tracking is removed from ram and a new set of training starts again
    at epoch 0. The result of the training is displayed and from there you can continue training if you wish.
    """
    while epochs > 0 :
        mygan.train(database,batch,50000,1000)
        mygan.save_model(filepath)
        np.savetxt(filepath + str(epochs) +'_d_losses.txt' ,mygan.g_losses)
        np.savetxt(filepath + str(epochs) +'_g_losses.txt' ,mygan.g_losses)
        mygan.d_losses,mygan.g_losses = [],[]
        epochs = epochs - 50000
        if epochs < 50000 and epochs > 0:
            print('almost done')
            mygan.train(database,batch,epochs,1000)
            break
        if epochs == 0:
            noise = np.random.normal(0, 1, (noise_dim,batch))
            generated_data = mygan.generator.predict(noise)
            print(generated_data)
            dagpolt(generated_data,database)
            calculate_fid(generated_data,database)
            epochs = int(input('continue?, enter n* of epochs'))

def run(mode):
    """
    This goes through and stores all the variables of dataGANclass
    then creates the GAN load weight if needed and trains the GAN.
    The options are fully explained on the README file.
    """
    #select datasettrained = abs(trained_fake - dataset)trained = abs(trained_fake - dataset)
    sets = input("set? 'w'/'i'/'p' ")
    if sets == 'i':
        database = datasets.load_iris()
        database = database.data
    elif sets == 'w':
        database = datasets.load_wine()
        database = database.data
    elif sets == 'p':
        database,mean,std = import_penguin('data/penguins_size.csv',False)
    else:
        return None
    #estract data
    batch = int(input('batch size? '))
    noise_dim = int(input('noise size? '))
    no_field = len(database[1])
    opti = input('opti? ')
    number_of_layers = int(input('layers? '))
    #create the GAN from the dataGAN
    use_model = input("model?: (w)gan /(g)an ")
    if use_model == 'g':
        mygan = dataGAN(opti,noise_dim,no_field,batch,number_of_layers)
        mygan.discriminator.summary()
    elif use_model == 'w':
        clip_threshold = float(input('clip threshold? '))
        mygan = wGAN(opti,noise_dim,no_field,batch,number_of_layers,clip_threshold)
        mygan.critic.summary()
    else:
        return None
    #print the stucture of the gan
    mygan.generator.summary()
    mygan.model.summary()
    #loads weights
    filepath = input("load filepath: (or n?) ")
    if filepath != 'n':
        try:
            mygan.load_weights(filepath)
        except OSError:# as 'Unable to open file':
            print('Error:404 file not found, starting from scratch')
    else:
        filepath = input('savepath? ')
    epochs = int(input('epochs? '))
    #marathon mode is not suitable when running less that 50000 epochs
    if epochs < 50000 and mode == 'm':
        print('epochs too small, switch to normal ')
        mode = 'n'
    if epochs > 0:
        step = int(ceil(epochs*0.01))
        if mode == 'm':
            marathon_mode(mygan,database,batch,noise_dim,filepath,epochs)
        else:
            # train the gan acorrding to the number of epochs
            mygan.train(database,batch,epochs,step)
        if mode == 's':
            # in spyder mode the gan model return so it can be expermented on
            return mygan,database
        else:
            mygan.save_model(filepath)
        show_loss_progress(mygan.d_losses,mygan.g_losses)
    samples = input('samples? ')
    original_data = database
    for s in range(int(samples)):
        generated_data = mygan.create_fake(batch)
        if sets == 'p':
            generated_data = unnormalize(generated_data,mean,std)
            original_data = unnormalize(database,mean,std)
        print(generated_data)
        dagpolt(generated_data,original_data)
        calculate_fid(generated_data,original_data)
    if mode == 's':
        return mygan

mode = input('mode?(s)pyder/(n)ormal/(m)arathon) ')
if mode == 's':
    gan,database = run(mode)
else:
    run(mode)
