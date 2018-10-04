import h5py
import os
from ..particles.particle import Particle
from ..particles.particle_chain import ParticleChain

class HDF5Storage(object):

    def __init__(self, h5_filename, mode):
        '''
        :param h5_filename: name of hdf5 file in which to save or from which
            to load a particle, a collection of particles, referred to as a
            particle step, or collection of steps, referred to as a particle
            chain.
        :type h5_filename: string
        :param mode: mode used when opening hdf5 file specified by h5_filename;
            can be 'w', 'r', 'r+', or 'a'. See h5py docs for details.
        :type mode: string
        '''
        self._h5 = h5py.File(h5_filename, mode=mode)
        self._mode = mode
        if 'steps' not in self._h5:
            self._step_parent_grp = self._h5.create_group('steps')
        else:
            self._step_parent_grp = self._h5['steps']


    def close(self,):
        self._h5.close()
        return None


    def get_num_steps(self,):
        '''
        Returns number of steps currently stored in the hdf5 file.
        '''
        return len(self._step_parent_grp.keys())


    def get_num_particles_in_step(self, step_index):
        '''
        Returns the number of particles in a particular step.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        '''
        step_name = 'step_%s' % step_index
        return len(self._step_parent_grp[step_name].keys())


    def write_particle(self, particle, step_index, particle_index):
        '''
        Writes a single particle object (params, weight and log likelihood)
        to the hdf5 file.

        :param particle: particle object storing a single parameter vector and
            associated weight and log likelihood.
        :type particle: Particle class instance
        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        :param particle_index: index of particle within a given step
        :type particle_index: integer
        '''
        step_name = 'step_%s' % step_index
        particle_name = 'particle_%s' % particle_index
        if not step_name in self._step_parent_grp:
            step_grp = self._create_step_group(step_index)
        else:
            step_grp = self._step_parent_grp[step_name]
        particle_grp = step_grp.create_group(particle_name)
        self._write_particle_params(particle.params, particle_grp)
        self._write_particle_weight(particle.weight, particle_grp)
        self._write_particle_log_like(particle.log_like, particle_grp)
        return None


    def read_particle(self, step_index, particle_index):
        '''
        Loads and returns a particle identified by specific step and particle
        indices.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        :param particle_index: index of particle within a given step
        :type particle_index: integer
        '''
        particle_grp = self._get_particle_group(step_index, particle_index)
        weight = particle_grp['weight'].value
        log_like = particle_grp['log_like'].value
        params_grp = particle_grp['parameters']
        params = {key: params_grp[key].value for key in params_grp.keys()}
        particle = Particle(params, weight, log_like)
        return particle


    def write_step(self, step, step_index):
        '''
        Writes a step, which is a collection of particles, to the hdf5 file.

        :param step: a list of particle objects, each of which stores a single
            parameter vector and associated weight and log likelihood.
        :type step: list of Particle class instances
        :param step_index: index of step being written
        :type step_index: integer
        '''
        step_name = 'step_%s' % step_index
        step_grp = self._create_step_group(step_index)
        for particle_index, particle in enumerate(step):
            self.write_particle(particle, step_index, particle_index)
        return None


    def read_step(self, step_index):
        '''
        Loads and returns a step (and all particles in that step) identified by         a specific step index.

        :param step_index: index of step that the particle belongs too
        :type step_index: integer
        '''
        step_grp = self._get_step_group(step_index)
        step = []
        for particle_name in step_grp.keys():
            particle_index = int(particle_name.split('_')[-1])
            step.append(self.read_particle(step_index, particle_index))
        return step


    def write_chain(self, particle_chain):
        '''
        Write a particle chain, which is a list of steps, each of which being a
        list of particles, to the hdf5 file.

        :param particle_chain: a list of steps, each of which is a list of
            particle objects.
        :type particle_chain: ParticleChain class instance
        '''
        for step_index, step in enumerate(particle_chain._steps):
            self.write_step(step, step_index)
        return None


    def read_chain(self,):
        '''
        Loads and returns an entire particle chain (which consists of all
        available steps and particles within each step).
        '''
        particle_chain = ParticleChain()
        for step_name in self._step_parent_grp.keys(): 
            step_index = int(step_name.split('_')[-1])
            step = self.read_step(step_index)
            particle_chain.add_step(step)
        return particle_chain


    def _create_step_group(self, step_index):
        self._step_parent_grp.create_group('step_%s' % step_index)
        return None


    def _write_particle_params(self, params, particle_grp):
        parameters_grp = particle_grp.create_group('parameters')
        for key, value in params.iteritems():
            parameters_grp.create_dataset(key, data=value, dtype=float)
        return None


    def _write_particle_weight(self, weight, particle_grp):
        particle_grp.create_dataset('weight', data=weight)
        return None


    def _write_particle_log_like(self, log_like, particle_grp):
        particle_grp.create_dataset('log_like', data=log_like)
        return None


    def _get_particle_group(self, step_index, particle_index):
        step_name = 'step_%s' % step_index
        particle_name = 'particle_%s' % particle_index
        path = os.path.join(step_name, particle_name)
        return self._step_parent_grp[path]


    def _get_step_group(self, step_index):
        step_name = 'step_%s' % step_index
        return self._step_parent_grp[step_name]
