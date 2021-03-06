import torch
import matplotlib
import numpy as np
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
import matplotlib.pyplot as plt
import copy

# For SAG and SAGA
def basic_train(epoch, dataloader, model, use_optimizer, optimizer, criterion, device, model_type, writer=None, update=2000, run_list=None):
    epoch_loss = 0
    running_loss = 0
    count = 0
    for i, data in enumerate(dataloader):
        optimizer.zero_grad()

        index, img, label = data
        index = index.item()

        if model_type == "MLP":
            img = img.view(img.shape[0], -1)
        
        img = img.to(device)
        label = label.to(device)

        output = model(img)

        loss = criterion(output, label)
        
        if use_optimizer in ['SAG', 'SAGA']:
            optimizer.set_step_information({'current_datapoint': index})
        
        if use_optimizer in ['Class_SAGA']:
            optimizer.set_step_information({'current_datapoint': label.cpu().item()})

        loss.backward()
        optimizer.step()
        
        loss = loss.detach().cpu().item()
        epoch_loss += loss
        running_loss += loss
        count += 1

        if i % update == update-1:
            print("Epoch: {} | Iteration {} | Loss: {}".format(epoch, i+1, running_loss/count))
            writer.add_scalar('Training Loss', running_loss/count, len(run_list)*update)
            run_list.append(running_loss/count)
            running_loss = 0
            count = 0
        
    return {'model': model, 'optimizer': optimizer, 'loss': epoch_loss/len(dataloader), 'run_list': run_list}

# FOR SVRG
def compute_full_grad(model, model_checkpoint, dataloader, model_type, criterion, device, optimizer, optimizer_checkpoint):
    print("Computing Full Gradient")
    # copy the latest "training model"
    model_checkpoint = copy.deepcopy(model)
    #print(model_checkpoint, "model_checkpoint !!!")
    # Get the full gradient and store it!
    for i, data in enumerate(dataloader):
        if i % 1000 == 0:
            print('{}/{}'.format(i, len(dataloader)))
        #print(len(data), " d a t a !!!")
        #print(data[0].shape, " d a t a 0 shape!!!")
        #print(data[1].shape, " d a t a 1 shape!!!")
        #print(data[2].shape, " d a t a 2 shape!!!")
        index, img, label = data

        if model_type == "MLP":
            img = img.view(img.shape[0], -1)
        
        img = img.to(device)
        label = label.to(device)

        output = model_checkpoint(img)

        loss = criterion(output, label)
        loss.backward()
        
        '''
        if i == 3000: #DELETE THIS LINE LATER
            print("break!!!")
            break
        '''
    # store into the "main model's" optimizer    
    optimizer.store_full_grad(list(model_checkpoint.parameters()))
    # clear the grads from the checkpoint model
    optimizer_checkpoint.zero_grad()

    return model, model_checkpoint, optimizer, optimizer_checkpoint

# FOR SVRG
def basic_svrg_train(epoch, dataloader, T, current_iteration, model, model_checkpoint, optimizer, optimizer_checkpoint,\
                     criterion, device, model_type, training=True, writer=None, update=2000, run_list=None):

    epoch_loss = 0
    running_loss = 0
    count = 0
    for i, data in enumerate(dataloader):
        
        optimizer.zero_grad()
        model_checkpoint.zero_grad()

        if current_iteration % T == 0:
            model, model_checkpoint, optimizer, optimizer_checkpoint = compute_full_grad(model, model_checkpoint, dataloader, model_type,\
                                                                                         criterion, device, optimizer, optimizer_checkpoint)

        index, img, label = data

        if model_type == "MLP":
            img = img.view(img.shape[0], -1)

        img = img.to(device)
        label = label.to(device)

        output = model(img)
        checkpoint_output = model_checkpoint(img)

        # get loss for the predicted output
        loss = criterion(output, label)
        checkpoint_loss = criterion(checkpoint_output, label)

        # get gradients w.r.t to parameters
        loss.backward()
        checkpoint_loss.backward()

        # store the current gradients of the checkpoint model
        optimizer.store_prev_grad(list(model_checkpoint.parameters()))
        optimizer.step()

        current_iteration += 1

        loss = loss.detach().cpu().item()
        epoch_loss += loss
        running_loss += loss
        count += 1
        
        #print(running_loss, " running_loss")
        #print(count, " count")
        #print(run_list, " run_list")
        if i % update == update-1:
            print("Epoch: {} | Iteration {} | Loss: {}".format(epoch, i+1, running_loss/count))
            writer.add_scalar('Training Loss', running_loss/count, len(run_list)*update)
            run_list.append(running_loss/count)
            running_loss = 0
            count = 0
        
    return {'model': model, 'optimizer': optimizer, 'model_checkpoint': model_checkpoint,\
            'optimizer_checkpoint':optimizer_checkpoint, 'current_iteration': current_iteration, 'loss': epoch_loss/len(dataloader),\
            'run_list': run_list}

# For SARAH
def compute_full_grad_SARAH(model, model_checkpoint, dataloader, model_type, criterion, device, optimizer):
    print("Computing Full Gradient")
    # copy the latest "training model"
    model_checkpoint = copy.deepcopy(model)
    #print(model_checkpoint, "model_checkpoint !!!")
    # Get the full gradient and store it!
    for i, data in enumerate(dataloader):
        if i % 1000 == 0:
            print('{}/{}'.format(i, len(dataloader)))
        index, img, label = data

        if model_type == "MLP":
            img = img.view(img.shape[0], -1)
        
        img = img.to(device)
        label = label.to(device)

        output = model_checkpoint(img)

        loss = criterion(output, label)
        loss.backward()
        
        '''
        if i == 3000: #DELETE THIS LINE LATER
            print("break!!!")
            break
        '''
    # store into the "main model's" optimizer    
    optimizer.store_full_grad(list(model_checkpoint.parameters()))
    # clear the grads from the checkpoint model
    #optimizer_checkpoint.zero_grad()
    model_checkpoint.zero_grad() 
    
    optimizer.one_step_GD()

    return model, model_checkpoint, optimizer

# TODO STILL NEED TO FIX THIS!
def basic_sarah_train(epoch, dataloader, T, current_iteration, model, model_checkpoint, optimizer,\
                     criterion, device, model_type, training=True, writer=None, update=2000, run_list=None, batch_sizes = 1):

    epoch_loss = 0
    running_loss = 0
    count = 0
    for i, data in enumerate(dataloader):
        
        model.zero_grad()
        model_checkpoint.zero_grad()

        if current_iteration % T == 0:
            model, model_checkpoint, optimizer = compute_full_grad_SARAH(model, model_checkpoint, dataloader, model_type,\
                                                                                         criterion, device, optimizer)       
        
        ### new training 
        index, img, label = data

        if model_type == "MLP":
             img = img.view(img.shape[0], -1)

        img = img.to(device)
        label = label.to(device)
          
        output = model(img)
        checkpoint_output = model_checkpoint(img)

        # get loss for the predicted output
        loss = criterion(output, label)
        checkpoint_loss = criterion(checkpoint_output, label)

        # get gradients w.r.t to parameters
        loss.backward()
        checkpoint_loss.backward()

        # store the current gradients of the checkpoint model
        optimizer.store_prev_grad(list(model_checkpoint.parameters()))
        model_checkpoint = copy.deepcopy(model)
        optimizer.step()

        current_iteration += 1

        loss = loss.detach().cpu().item()
        epoch_loss += loss
        running_loss += loss
        count += 1

        if i % update == update-1:
            print("Epoch: {} | Iteration {} | Loss: {}".format(epoch, i+1, running_loss/count))
            writer.add_scalar('Training Loss', running_loss/count, len(run_list)*update)
            run_list.append(running_loss/count)
            running_loss = 0
            count = 0

#         optimizer.store_prev_grad(list(model_checkpoint.parameters()))
#         model_checkpoint =  copy.deepcopy(model)
        # update parameters
#         optimizer.step()
#         model_checkpoint =  copy.deepcopy(model)

        #print('epoch {}, loss {}'.format(epoch, loss.item()))
        
    return {'model': model, 'optimizer': optimizer, 'model_checkpoint': model_checkpoint,\
             'current_iteration': current_iteration, 'loss': epoch_loss/len(dataloader),\
            'run_list': run_list}
